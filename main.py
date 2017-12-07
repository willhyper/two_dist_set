#!/Users/chaoweichen/anaconda/bin/python
'''
strongly regular graph generator
http://www.win.tue.nl/~aeb/graphs/srg/srgtab.html

65 32 15 16

'''
from two_dist_set import strong_graph
from pprint import pprint


if __name__ == '__main__':

    import sys
    v, k, l, u = map(int, sys.argv[1:5])

    assert strong_graph.check_problem(v,k,l,u), f'{(v,k,l,u)} is not a strongly regular graph problem.'
    seed = strong_graph.generate_seed(v,k,l,u)

    ans = list(strong_graph.generate(seed, v, k, l, u))
    pprint(ans)
