__author__ = 'chaoweichen'
from collections import deque
from . import candidates

def generate(A):
    q = deque()
    q.append(A)
    v = len(A[0])+1
    while q:
        simple_sym_graph = q.pop()
        if len(simple_sym_graph) == v - 1:
            yield simple_sym_graph # weak
        else:
            for g in advance_simple_sym_graph(simple_sym_graph):
                q.append(g)

def advance_simple_sym_graph(A):
    for c in candidates.generate(A):
        AA = tuple(A) + (tuple(c),)
        yield AA
