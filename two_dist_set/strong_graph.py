__author__ = 'chaoweichen'
import numpy as np
from . import representation
from . import weak_graph
from collections import deque

def check_problem(v, k, l, u):
    return (v - k - 1) * u == k * (k - l - 1)


def generate_seed(v, k, l, u):
    return 2 ** (v - 1) - 2 ** (v - k - 1),  # tuple of numbers


def generate(seed, v, k, l, u):
    q = deque()
    q.append(seed) # seed = (240, 76, 3)

    while q:
        graph = q.pop()

        if len(graph) == v - 1:  # data structure property. when met, graph is complete
            yield representation.from_scalars(graph,v,k,l,u).to_matrix()
        else:
            M = representation.from_scalars(graph, v, k, l, u).to_matrix()
            row = len(graph)
            cumsum_len = v - row - 1

            weak_candidates = weak_graph._satisfy_weak_condition(graph, v, k, l, u)
            for dec in weak_candidates:
                binn = np.array(representation.dec2bin(dec, cumsum_len), dtype=np.int)
                for xx in range(row):
                    inprod = l if M[xx, row] == 1 else u
                    rem = inprod - M[row, 0:row].dot(M[xx, 0:row])
                    if binn.dot(M[xx, -cumsum_len:]) != rem:
                        break
                else:
                    q.append(graph + (dec,))

