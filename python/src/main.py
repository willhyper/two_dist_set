#!/Users/chaoweichen/anaconda/bin/python
'''
strongly regular graph generator
http://www.win.tue.nl/~aeb/graphs/srg/srgtab.html


13 6 2 3
15 6 1 3
15 8 4 4
65 32 15 16

'''
from two_dist_set import strong_graph, globalz
from pprint import pprint


if __name__ == '__main__':

    import sys
    v, k, l, u = map(int, sys.argv[1:5])
    globalz.set_problem(v, k, l, u)
    seed = globalz.generate_seed()
    #seed = (4032, 1592, 294, 149)#, 77, 99, 26, 11, 14, 1, 3, 0)

    for ans in strong_graph.generate(seed=seed):
        pprint(ans)

