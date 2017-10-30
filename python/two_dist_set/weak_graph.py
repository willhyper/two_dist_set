__author__ = 'chaoweichen'
from collections import deque
from . import candidates
from . import representation

def generate(A):
    q = deque()
    q.append(A)
    v = representation.from_scalars(A).v

    while q:
        simple_sym_graph = q.pop()
        if len(simple_sym_graph) == v - 1:
            yield simple_sym_graph # weak
        else:
            for g in advance_simple_sym_graph(simple_sym_graph):
                q.append(g)

def advance_simple_sym_graph(A):
    for c in candidates.generate(A):
        AA = A + (c,)
        yield AA
