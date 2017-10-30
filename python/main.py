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

if __name__ == '__main__':

    import sys

    v, k, l, u = map(int, sys.argv[1:5])

    A = tuple(1 if i < k else 0 for i in range(v - 1))
    A = (A,)  # tuple in a tuple

    assert len(A[0]) == v - 1

    for ans in strong_graph.generate(seed=A, v=v, k=k, l=l, u=u):
        print(ans)
