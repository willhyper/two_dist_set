#!python
#cython: language_level=3
from srg import util, strong_graph
from pprint import pprint
import time
import sys


if __name__ == '__main__':

    v, k, l, u = list(map(int, sys.argv[1:5]))
    util.assert_arg(v, k, l, u)
    seed = util.generate_seed(v, k, l, u)

    srg_solved = []
    start = time.time()
    start_dummy = start
    for s in strong_graph.solve(seed):
        now = time.time()
        elapsed_s, start = now - start, now
        mat = s.to_matrix()
        pprint(mat)
        print(f'elapsed {elapsed_s} s')
        srg_solved.append(s)

    elapsed_total = time.time() - start_dummy

    print('sorted matrix')
    srg_solved.sort()

    matricies = [s.to_matrix() for s in srg_solved]
    pprint(matricies)

    print(f'totally elapsed {elapsed_total} s')
