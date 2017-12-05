__author__ = 'chaoweichen'
from collections import deque
from . import candidates

def generate(A, v, k, l, u):
    q = deque()
    q.append(A)

    while q:
        simple_sym_graph = q.pop()
        if len(simple_sym_graph) == v - 1:
            # print(len(q), simple_sym_graph)
            yield simple_sym_graph # weak
        else:
            weak_candidates = sorted(candidates.generate(simple_sym_graph,v,k,l,u))
            for c in weak_candidates:
                q.append( simple_sym_graph + (c,))
