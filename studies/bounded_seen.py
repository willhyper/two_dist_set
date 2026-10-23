"""Compare exact solutions and timings for the bounded-seen experiment.

PYTHONPATH=src python -O studies/bounded_seen.py       # default cache
PYTHONPATH=src python -O studies/bounded_seen.py 128   # aggressive eviction
Run the same script from baseline master for comparison (without a capacity).
CPU excludes the manager and worker startup; see bounded_seen_results.json.
"""
import json,sys,time
from srg import parallel,solver,canon
from srg.model import PartialSRG
from srg.database import get_solutions
if __name__=='__main__':
 for quest in [(21,10,4,5),(36,14,7,4)]:
  start=time.monotonic();cpu=time.process_time();messages=[]
  kwargs={'seen_capacity':int(sys.argv[1])} if len(sys.argv)>1 else {}
  found=list(parallel.solve_parallel(PartialSRG(solver._seed(*quest)),max_solutions=None,workers=2,progress=messages.append,**kwargs))
  used=time.process_time()-cpu+parallel.worker_cpu_seconds
  keys=[canon.canonical_key(m,10**7) for m in found]
  expected={canon.canonical_key(m,10**7) for m in get_solutions(*quest)}
  if len(keys)!=len(set(keys)) or set(keys)!=expected:raise RuntimeError("solution mismatch")
  print(json.dumps({'quest':quest,'cpu':used,'wall':time.monotonic()-start,'solutions':len(found),'last':messages[-1]}),flush=True)
