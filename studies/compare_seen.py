"""Run the 29 benchmark quests: paired exactness/CPU/RSS comparison on macOS.

Run from packed-seen with a persistent output directory:
  python studies/compare_seen.py --output ~/.srg_runs/packed_seen_benchmark --workers 14

Each solve runs in a fresh Python process. Full canonical matrix bytes (not
hash digests) must equal the saved database solution set, with no duplicates;
every returned matrix must pass PartialSRG.solved(). CPU covers the timed
solve's parent plus reaped children, including manager and worker startup.
Combined process-tree RSS and manager RSS are sampled externally every 20 ms
using macOS libproc. RSS can double-count shared pages and miss short peaks.
Memory sampling covers process startup through validation/exit. Wall time is
solve-only. Existing CPU/memory load affects both branches. No source changes
or database performance updates are made by this benchmark.
"""
import argparse
import ctypes
import importlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import time

BENCHMARK_QUESTS = [
 (4,2,0,2),(5,2,0,1),(9,4,1,2),(10,3,0,1),(10,6,3,4),
 (12,6,0,6),(13,6,2,3),(15,6,1,3),(15,8,4,4),(16,5,0,2),
 (16,6,2,2),(16,9,4,6),(16,10,6,6),(17,8,3,4),(21,10,3,6),
 (21,10,4,5),(21,10,5,4),(25,8,3,2),(25,12,5,6),(25,16,9,12),
 (26,10,3,4),(27,10,1,5),(28,9,0,4),(28,12,6,4),(36,10,4,2),
 (36,14,7,4),(49,12,5,2),(50,7,0,1),(50,21,4,12),
]
ROOTS = {'master':Path('/Users/willhyper/repo/two_dist_set'),
         'packed-seen':Path('/Users/willhyper/repo/two_dist_set_packed_seen')}


def total_cpu():
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + child.ru_utime + child.ru_stime


def worker(args):
    from multiprocessing.managers import BaseManager
    from srg import canon, parallel, solver
    from srg.model import PartialSRG
    quest = tuple(map(int, args.quest.split(',')))
    module = importlib.import_module('srg.database.problem_'+'_'.join(map(str,quest)))
    from srg.database import get_solutions
    expected = get_solutions(*quest)
    # Hook manager startup solely to expose its PID to the external sampler.
    original_start = BaseManager.start
    def start(manager, *pos, **kw):
        result = original_start(manager, *pos, **kw)
        Path(args.pid_file).write_text(str(manager._process.pid))
        return result
    BaseManager.start = start
    started = time.perf_counter()
    cpu_start = total_cpu()
    found = list(parallel.solve_parallel(
        PartialSRG(solver._seed(*quest)), max_solutions=None, workers=args.workers))
    cpu = total_cpu() - cpu_start
    wall = time.perf_counter() - started
    if not all(PartialSRG(m).solved() for m in found):
        raise RuntimeError('invalid solved matrix')
    # Canonical matrices avoid the finite canonical_key leaf budget. Compare
    # every byte and retain the exact representations for cross-branch checks.
    found_keys = [canon.canonical_matrix(m).tobytes().hex() for m in found]
    expected_keys = [canon.canonical_matrix(m).tobytes().hex() for m in expected]
    if len(found_keys) != len(set(found_keys)):
        raise RuntimeError('duplicate canonical solutions')
    if len(expected_keys) != len(set(expected_keys)):
        raise RuntimeError('database contains duplicate canonical solutions')
    if set(found_keys) != set(expected_keys):
        raise RuntimeError('canonical solution set differs from database')
    Path(args.result_file).write_text(json.dumps({
        'quest':quest, 'source':parallel.__file__, 'solutions':len(found),
        'exact':True, 'canonical_solutions':sorted(found_keys),
        'cpu_sec':cpu, 'wall_sec':wall,
        'worker_slice_cpu_sec':parallel.worker_cpu_seconds,
        'stored_cpu_sec':getattr(module,'cpu_sec',None),
    }))


class TaskInfo(ctypes.Structure):
    # Exact layout from macOS SDK sys/proc_info.h, struct proc_taskinfo.
    _fields_ = [(name,ctypes.c_uint64) for name in
                ('virtual','resident','user','system','threads_user','threads_system')] + [
                ('counters',ctypes.c_int32 * 12)]


class Sampler:
    def __init__(self):
        self.lib = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
        self.lib.proc_listpids.argtypes = [ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_int]
        self.lib.proc_listpids.restype = ctypes.c_int
        self.lib.proc_pidinfo.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int]
        self.lib.proc_pidinfo.restype = ctypes.c_int
        if self.rss(os.getpid()) is None:
            raise RuntimeError('libproc cannot read RSS; run with process-inspection access')

    def children(self,pid):
        # PROC_PPID_ONLY = 6; proc_listpids returns bytes of PID data.
        buffer = (ctypes.c_int * 1024)()
        size = self.lib.proc_listpids(6,pid,buffer,ctypes.sizeof(buffer))
        if size < 0: return []
        if size >= ctypes.sizeof(buffer):
            raise RuntimeError('child PID buffer full')
        return [p for p in buffer[:size//ctypes.sizeof(ctypes.c_int)] if p>0]

    def rss(self,pid):
        info = TaskInfo()
        size = self.lib.proc_pidinfo(pid,4,0,ctypes.byref(info),ctypes.sizeof(info))
        return info.resident if size == ctypes.sizeof(info) else None

    def tree(self,pid):
        todo=[pid];seen=set();total=0;count=0
        while todo:
            current=todo.pop()
            if current in seen:continue
            seen.add(current)
            rss=self.rss(current)
            if rss is not None:total+=rss;count+=1
            todo.extend(self.children(current))
        return total,count


def git(root,*arguments):
    return subprocess.check_output(['git','-C',str(root),*arguments],text=True).strip()


def main(args):
    global ROOTS
    ROOTS = {'master': Path(args.master_root).resolve(), 'packed-seen': Path(args.packed_root).resolve()}
    output=Path(args.output).expanduser();output.mkdir(parents=True,exist_ok=True)
    sampler=Sampler()
    metadata={
        'created_at':time.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'workers':args.workers,'python':sys.version,'interval_sec':args.interval,
        'branches':{name:{'root':str(root),'commit':git(root,'rev-parse','HEAD')}
                    for name,root in ROOTS.items()},
        'notes':__doc__, 'python_hash_seed':'0',
        'blas_thread_limit':'1', 'quest_count':len(BENCHMARK_QUESTS),
    }
    (output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    rows=[]
    for index,quest in enumerate(BENCHMARK_QUESTS):
        name='problem_'+'_'.join(map(str,quest))
        order=['master','packed-seen'] if index%2==0 else ['packed-seen','master']
        pair={}
        for branch in order:
            root=ROOTS[branch];prefix=output/(name+'_'+branch)
            result_path=Path(str(prefix)+'.json');pid_path=Path(str(prefix)+'.pid')
            # Do not silently reuse an unrelated result or stale PID file.
            if result_path.exists() or pid_path.exists():
                raise RuntimeError('output already exists: '+str(prefix))
            env=dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONHASHSEED='0',
                     PYTHONWARNINGS='ignore',OPENBLAS_NUM_THREADS='1',
                     VECLIB_MAXIMUM_THREADS='1',OMP_NUM_THREADS='1')
            manager=None;peak=manager_peak=count_peak=samples=0
            with open(str(prefix)+'.out','w') as stdout,open(str(prefix)+'.err','w') as stderr:
                process=subprocess.Popen([
                    sys.executable,'-O',str(Path(__file__).resolve()),'--worker',
                    '--quest',','.join(map(str,quest)),'--workers',str(args.workers),
                    '--pid-file',str(pid_path),'--result-file',str(result_path)],
                    cwd=root,env=env,stdout=stdout,stderr=stderr)
                while process.poll() is None:
                    if manager is None and pid_path.exists():
                        try:manager=int(pid_path.read_text())
                        except ValueError:pass
                    rss,count=sampler.tree(process.pid)
                    peak=max(peak,rss);count_peak=max(count_peak,count);samples+=1
                    if manager is not None:manager_peak=max(manager_peak,sampler.rss(manager) or 0)
                    time.sleep(args.interval)
                if process.returncode:
                    raise RuntimeError(f'{branch} {name} failed; inspect {prefix}.err')
            row=json.loads(result_path.read_text())
            expected_source=str(root/'src/srg/parallel.py')
            if row['source'] != expected_source:raise RuntimeError('wrong source tree: '+row['source'])
            row.update(branch=branch,peak_tree_rss_mib=peak/1024**2,
                       peak_manager_rss_mib=manager_peak/1024**2,
                       max_processes=count_peak,memory_samples=samples)
            if not peak or not manager_peak:raise RuntimeError('missing RSS measurement')
            result_path.write_text(json.dumps(row,indent=2)+'\n')
            pair[branch]=row
            rows.append(row)
            with open(output/'results.jsonl','a') as file:file.write(json.dumps(row)+'\n')
            small={k:v for k,v in row.items() if k not in ('canonical_solutions','source')}
            print(json.dumps(small),flush=True)
        if pair['master']['canonical_solutions'] != pair['packed-seen']['canonical_solutions']:
            raise RuntimeError('cross-branch solution mismatch for '+name)
        (output/'progress.json').write_text(json.dumps({'completed_pairs':index+1,'total_pairs':len(BENCHMARK_QUESTS),'last_quest':quest})+'\n')
    print('ALL_29_PAIRS_EXACT',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--output')
    parser.add_argument('--master-root',default=str(Path(__file__).resolve().parents[1].parent/'two_dist_set'))
    parser.add_argument('--packed-root',default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--workers',type=int,default=14)
    parser.add_argument('--interval',type=float,default=0.02)
    parser.add_argument('--quest')
    parser.add_argument('--pid-file')
    parser.add_argument('--result-file')
    args=parser.parse_args()
    if args.worker:worker(args)
    else:main(args)
