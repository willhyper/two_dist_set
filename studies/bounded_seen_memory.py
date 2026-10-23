"""Synthetic peak-RSS comparison, run each mode in a separate process.

PYTHONPATH=src python studies/bounded_seen_memory.py unbounded
PYTHONPATH=src python studies/bounded_seen_memory.py bounded
macOS ru_maxrss is measured in bytes. This is not a quest memory benchmark.
"""
import resource,sys,time,json
from srg import parallel
mode=sys.argv[1]
cache={} if mode=='unbounded' else parallel._SeenCache(250_000)
start=time.monotonic()
for i in range(1_000_000):
 cache.setdefault((9,i.to_bytes(32,'big')), (1,1))
print(json.dumps({'mode':mode,'keys_retained':len(cache) if isinstance(cache,dict) else cache.size(),'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,'seconds':time.monotonic()-start}))
