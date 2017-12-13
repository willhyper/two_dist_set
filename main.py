#!/Users/chaoweichen/anaconda/bin/python
'''
strongly regular graph generator
http://www.win.tue.nl/~aeb/graphs/srg/srgtab.html

65 32 15 16

'''
from two_dist_set import strong_graph
from pprint import pprint
import time

from two_dist_set.srg import SRG

if __name__ == '__main__':

    import sys

    v, k, l, u = map(int, sys.argv[1:5])

    strong_graph.assert_arg(v, k, l, u)

    srg = SRG(v, k, l, u)
    seed = strong_graph.generate_seed(v, k, l, u)
    srg.add(seed)

    ans = []
    start = time.time()
    for s in strong_graph.generate(srg):
        now = time.time()
        elapsed_s, start = now - start, now
        print(s, 'elapsed', elapsed_s)
        ans.append(s)

    pprint(ans)
