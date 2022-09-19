#!python
#cython: language_level=3
'''
strongly regular graph generator
http://www.win.tue.nl/~aeb/graphs/srg/srgtab.html
http://www.maths.gla.ac.uk/~es/srgraphs.php

65 32 15 16

'''
from two_dist_set import util, strong_graph
from two_dist_set import database as db
from pprint import pprint
import time

import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compute and draw strongly regular graphes (SRG).')
    parser.add_argument('-p', metavar=('v', 'k', 'l', 'u'), type=int, nargs=4,
                        help='4 integers representing v, k, l, u, defining a SRG')
    parser.add_argument('-d', '--draw', action='store_true', help='output png of the SRG if defined in database.')
    parser.add_argument('-l', '--list', action='store_true', help='list SRG in database')
    args = parser.parse_args()


    if args.list:
        pprint(db.list_problems())
    elif args.draw:
        print('draw', args.p)
        v, k, l, u = args.p
        util.assert_arg(v, k, l, u)
        matricies = db.get_solutions(v, k, l, u)
        util.draw(v,k,l,u, matricies)
    else:

        v, k, l, u = args.p
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
