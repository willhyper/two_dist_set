#!/Users/chaoweichen/anaconda/bin/python
'''
strongly regular graph generator
http://www.win.tue.nl/~aeb/graphs/srg/srgtab.html

4 2 0 2 : 0.5s
5 2 0 1: 0.262s
9 4 1 2: 0.549s
10 3 0 1: 0.559s
10 6 3 4: 2.24s
13 6 2 3
15 6 1 3

'''
from two_dist_set import strong_graph
from two_dist_set import representation

if __name__ == '__main__':

    import sys

    v, k, l, u = map(int, sys.argv[1:5])

    A = (2**(v-1) - 2**(v-k-1),)  # tuple of numbers

    for ans in strong_graph.generate(seed=A, v=v, k=k, l=l, u=u):
        print(ans)
