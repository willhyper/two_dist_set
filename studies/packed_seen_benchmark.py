"""Exact solution-set and solver timing comparison for packed seen keys.

PYTHONPATH=src python -O studies/packed_seen_benchmark.py
Run this same script against master and packed-seen source trees.
CPU includes parent plus reaped child user/system time, including the manager.
Two workers; wall time includes canonical validation. Single samples on a
busy machine are not evidence of a speedup.
"""
import json,sys,time,resource
def total_cpu():
 children=resource.getrusage(resource.RUSAGE_CHILDREN)
 return time.process_time()+children.ru_utime+children.ru_stime

from srg import parallel,solver,canon
from srg.model import PartialSRG
from srg.database import get_solutions
if __name__=='__main__':
 for quest in [(21,10,4,5),(36,14,7,4)]:
  expected={canon.canonical_key(m,10**7) for m in get_solutions(*quest)}
  start=time.monotonic();cpu=total_cpu();messages=[]
  kwargs={}
  found=list(parallel.solve_parallel(PartialSRG(solver._seed(*quest)),max_solutions=None,workers=2,progress=messages.append,**kwargs))
  used=total_cpu()-cpu
  keys=[canon.canonical_key(m,10**7) for m in found]
  expected={canon.canonical_key(m,10**7) for m in get_solutions(*quest)}
  if len(keys)!=len(set(keys)) or set(keys)!=expected:raise RuntimeError("solution mismatch")
  print(json.dumps({'quest':quest,'cpu':used,'wall':time.monotonic()-start,'solutions':len(found),'last':messages[-1]}),flush=True)
