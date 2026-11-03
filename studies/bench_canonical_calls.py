"""Benchmark key calls on actual feasible SRG(36,14,4,6) candidates plus banked prefixes.

Captures a separate short worker slice, never attaches to the ongoing quest.
Checks every exact byte result before timing. Includes Python/Rust conversion
and FFI costs. Alternates execution order; reports process CPU rather than wall.
"""
import argparse
import json
import statistics
import time
from collections import Counter
from pathlib import Path

from srg import canon, database, parallel, solver
from srg.seen import SharedSeen


def run(args):
    if canon._rust_canonical is None:
        raise RuntimeError('build Rust first, then run with SRG_CANON_BACKEND=auto or rust')
    matrices=[]
    original=canon.canonical_key
    def capture(matrix,*pos,**kw):
        if len(matrices)<4096:matrices.append(matrix.copy())
        return original(matrix,*pos,**kw)
    canon.canonical_key=capture
    try:
        parallel.work(((36,14,4,6),[solver._seed(36,14,4,6)],args.sample_seconds,True,SharedSeen()))
    finally:
        canon.canonical_key=original
    for matrix in database.get_solutions(36,14,4,6):
        matrices.extend(matrix[:rows].copy() for rows in range(2,37))
    expected=[canon._canonical_python(matrix,5000) for matrix in matrices]
    assert [canon._rust_canonical(matrix,5000) for matrix in matrices]==expected
    timings={'python':[],'rust':[]}
    implementations={'python':canon._canonical_python,'rust':canon._rust_canonical}
    for trial in range(args.repeats):
        for name in (['python','rust'] if trial%2==0 else ['rust','python']):
            function=implementations[name]
            started=time.process_time()
            actual=[function(matrix,5000) for matrix in matrices]
            elapsed=time.process_time()-started
            assert actual==expected
            timings[name].append(elapsed)
    result=dict(quest=[36,14,4,6],sample_seconds=args.sample_seconds,repeats=args.repeats,
                calls_per_trial=len(matrices),rows=dict(sorted(Counter(m.shape[0] for m in matrices).items())),
                exact=True,none_returns=sum(k is None for k in expected),cpu_seconds=timings,
                median_cpu_seconds={name:statistics.median(t) for name,t in timings.items()})
    result['speedup']=result['median_cpu_seconds']['python']/result['median_cpu_seconds']['rust']
    result['median_microseconds_per_call']={name:sec*1e6/len(matrices) for name,sec in result['median_cpu_seconds'].items()}
    Path(args.output).write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample-seconds',type=float,default=10)
    parser.add_argument('--repeats',type=int,default=5)
    parser.add_argument('--output',required=True)
    run(parser.parse_args())
