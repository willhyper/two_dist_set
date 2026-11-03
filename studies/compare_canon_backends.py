"""Paired Python/Rust solves of the 29 benchmark quests, exactness first.

Requires python build_rust.py. Run in the matching Python environment:
  PYTHONPATH=src python studies/compare_canon_backends.py --output ~/.srg_runs/canon_comparison --workers 4

Both backends use the same source tree, Python/NumPy, worker count and settings.
Alternates which backend runs first. Full canonical certificates from the
Python reference are the oracle, including all zero-solution quests. Timings
exclude validation and include parent, manager, workers and process startup
inside solve. RSS is sampled process-tree RSS on macOS, not unique physical RAM.
One paired pass under concurrent system load is not a statistical speed claim.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

from compare_seen import BENCHMARK_QUESTS, Sampler


def total_cpu():
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + children.ru_utime + children.ru_stime


def worker(args):
    from srg import canon, database, parallel, solver
    from srg.model import PartialSRG
    quest = tuple(args.quest)
    snapshots = []
    started, cpu_start = time.perf_counter(), total_cpu()
    found = list(parallel.solve_parallel(PartialSRG(solver._seed(*quest)),
                 max_solutions=None, workers=args.workers, dedup_progress=snapshots.append))
    cpu, wall = total_cpu()-cpu_start, time.perf_counter()-started
    assert canon.CANON_BACKEND == os.environ['SRG_CANON_BACKEND']
    assert all(PartialSRG(matrix).solved() for matrix in found)
    def keys(matrices):
        result = [canon._canonical_python(m, 10**7) for m in matrices]
        assert all(k is not None for k in result)
        assert len(result) == len(set(result))
        return sorted(k.hex() for k in result)
    actual, expected = keys(found), keys(database.get_solutions(*quest))
    assert actual == expected, quest
    Path(args.result).write_text(json.dumps(dict(quest=quest, backend=canon.CANON_BACKEND,
        exact=True, solutions=len(found), canonical_keys=actual, cpu_sec=cpu, wall_sec=wall,
        dedup=snapshots[-1], python=sys.version)))


def run(args):
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    files = [root/'src/srg/canon.py',root/'src/srg/_canon_native.py',root/'rust/canon/src/lib.rs',root/'rust/canon/Cargo.lock']
    metadata = dict(created_at=time.strftime('%Y-%m-%d %H:%M:%S %Z'), workers=args.workers,
        source=str(root), notes=__doc__, python=sys.version,
        sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (output/'metadata.json').write_text(json.dumps(metadata,indent=2))
    sampler = Sampler()
    results = []
    for index,quest in enumerate(BENCHMARK_QUESTS):
        pair = {}
        name='problem_'+'_'.join(map(str,quest))
        for backend in (['python','rust'] if index%2==0 else ['rust','python']):
            result = output/(name+'_'+backend+'.json')
            env=dict(os.environ,PYTHONPATH=str(root/'src'),SRG_CANON_BACKEND=backend,
                     OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTHONHASHSEED='0')
            command=[sys.executable,str(Path(__file__).resolve()),'--worker','--workers',str(args.workers),
                     '--quest',*map(str,quest),'--result',str(result)]
            peak=0
            with (output/(name+'_'+backend+'.err')).open('w') as error:
                process=subprocess.Popen(command,cwd=str(root),env=env,stderr=error)
                while process.poll() is None:
                    rss,_=sampler.tree(process.pid);peak=max(peak,rss)
                    time.sleep(.02)
                if process.returncode:
                    raise RuntimeError(f'{name} {backend} failed: see {error.name}')
            data=json.loads(result.read_text());data['peak_combined_rss_mib']=peak/1024**2
            result.write_text(json.dumps(data,indent=2));pair[backend]=data
        assert pair['python']['canonical_keys']==pair['rust']['canonical_keys']
        row=dict(quest=name,solutions=pair['python']['solutions'],exact=True,
                 python_cpu_sec=pair['python']['cpu_sec'],rust_cpu_sec=pair['rust']['cpu_sec'],
                 python_wall_sec=pair['python']['wall_sec'],rust_wall_sec=pair['rust']['wall_sec'],
                 python_peak_rss_mib=pair['python']['peak_combined_rss_mib'],
                 rust_peak_rss_mib=pair['rust']['peak_combined_rss_mib'])
        results.append(row)
        with (output/'summary.csv').open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(row));writer.writeheader();writer.writerows(results)
        print(json.dumps(row),flush=True)
    totals=dict(quests=len(results),all_exact=all(r['exact'] for r in results),solutions=sum(r['solutions'] for r in results),
                python_cpu_sec=sum(r['python_cpu_sec'] for r in results),rust_cpu_sec=sum(r['rust_cpu_sec'] for r in results),
                python_peak_rss_mib=max(r['python_peak_rss_mib'] for r in results),
                rust_peak_rss_mib=max(r['rust_peak_rss_mib'] for r in results))
    (output/'totals.json').write_text(json.dumps(totals,indent=2));print(json.dumps(totals),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--quest',type=int,nargs=4)
    parser.add_argument('--result')
    parser.add_argument('--output')
    args=parser.parse_args()
    if args.worker:worker(args)
    else:
        if not args.output:parser.error('--output is required')
        run(args)
