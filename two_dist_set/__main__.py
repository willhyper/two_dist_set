#!/Users/chaoweichen/anaconda/bin/python
'''
strongly regular graph generator
http://www.win.tue.nl/~aeb/graphs/srg/srgtab.html

65 32 15 16

'''
from . import srg, util
from pprint import pprint
import time


if __name__ == '__main__':

    import sys

    v, k, l, u = map(int, sys.argv[1:5])

    util.assert_arg(v, k, l, u)

    seed = util.generate_seed(v, k, l, u)

    ans = []
    start = time.time()
    start_dummy = start
    for s in srg.solve(seed):
        now = time.time()
        elapsed_s, start = now - start, now
        pprint(s)
        print(f'elapsed {elapsed_s} s')
        ans.append(s)

    elapsed_total = time.time() - start_dummy
    pprint(ans)

    print(f'totally elapsed {elapsed_total} s')
