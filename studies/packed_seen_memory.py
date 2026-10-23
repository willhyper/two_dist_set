"""Compare exact retention of five-byte keys in separate macOS processes.

PYTHONPATH=src python studies/packed_seen_memory.py dict
PYTHONPATH=src python studies/packed_seen_memory.py packed
Optional second argument is the number of keys (default 1000000).
ru_maxrss is bytes on macOS. Baseline reuses one ownership tuple, so it
underestimates the live manager's per-entry ownership-object overhead.
This is synthetic storage RSS, not an end-to-end quest memory measurement.
"""
import json,resource,sys,time
from srg.seen import SharedSeen
if __name__=='__main__':
 mode=sys.argv[1]; count=int(sys.argv[2]) if len(sys.argv)>2 else 1000000
 store={} if mode=='dict' else SharedSeen()
 t=time.perf_counter()
 for i in range(count):
  key=i.to_bytes(5,'big')
  if mode=='dict':store.setdefault((2,key),(1,1))
  elif not store.claim(2,key):raise RuntimeError('lost new key')
 insert=time.perf_counter()-t;t=time.perf_counter()
 for i in range(count):
  key=i.to_bytes(5,'big')
  if mode=='dict':
   if (2,key) not in store:raise RuntimeError('missing key')
  elif store.claim(2,key):raise RuntimeError('missing key')
 print(json.dumps({'mode':mode,'count':count,'insert_seconds':insert,'lookup_seconds':time.perf_counter()-t,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,'stats':None if mode=='dict' else store.stats()}),flush=True)
