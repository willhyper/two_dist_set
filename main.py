#!/Users/chaoweichen/anaconda/bin/python
'''
strongly regular graph generator
http://www.win.tue.nl/~aeb/graphs/srg/srgtab.html


13 6 2 3
15 6 1 3
15 8 4 4
65 32 15 16

'''
from two_dist_set import strong_graph
from pprint import pprint


if __name__ == '__main__':

    import sys
    v, k, l, u = map(int, sys.argv[1:5])

    assert strong_graph.check_problem(v,k,l,u), f'{(v,k,l,u)} is not a strongly regular graph problem.'
    seed = strong_graph.generate_seed(v,k,l,u)

    #seed = (4032, 1592, 294, 149)#, 77, 99, 26, 11, 14, 1, 3, 0)

    for ans in strong_graph.generate(seed, v, k, l, u):
        pprint(ans)

