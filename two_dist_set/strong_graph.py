__author__ = 'chaoweichen'
import numpy as np
from . import representation
from . import weak_graph
from collections import deque

def assert_arg(v, k, l, u):
    assert (v - k - 1) * u == k * (k - l - 1), f'{(v,k,l,u)} is not a strongly regular graph problem.'

def generate_seed(v, k, l, u):
    return 2 ** (v - 1) - 2 ** (v - k - 1),  # tuple of numbers

def assert_strong(mat, v, k, l, u):
    assert_arg(v, k, l, u)

    I = np.identity(v, dtype=np.int)
    J = np.ones((v, v), dtype=np.int)
    const = (k-u)*I + u*J
    assert np.array_equal(mat@mat - (l-u)*mat , const)

    det = np.rint(np.linalg.det(mat))
    assert det == determinant(v,k,l,u)

def conference(v,k,l,u):
    return 2*k + (v-1)*(l-u)

def eig(v,k,l,u):
    conf = conference(v,k,l,u) # if conference graph, conf == 0, so D becomes non-integer

    D = np.sqrt((l-u)**2 + 4*(k-u))
    D = int(D) if conf!=0 else D

    eig = k, ((l-u) + D)/2, ((l-u) - D)/2
    eig = tuple(int(x) if conf !=0 else x for x in eig) # if not conference graph, eigvalues are integer
    mul = 1, int(((v-1) - conf/D)/2), int(((v-1) + conf/D)/2) # multiplicity is always integer

    return tuple(zip(eig, mul))

def determinant(v,k,l,u):
    prod = 1
    for e, m in eig(v,k,l,u):
        prod *= e**m

    return int(round(prod))


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

            weak_candidates = weak_graph.generate(graph, v, k)
            for dec in weak_candidates:
                binn = np.array(representation.dec2bin(dec, cumsum_len), dtype=np.int)
                for xx in range(row):
                    inprod = l if M[xx, row] == 1 else u
                    rem = inprod - M[row, 0:row].dot(M[xx, 0:row])
                    if binn.dot(M[xx, -cumsum_len:]) != rem:
                        break
                else:
                    q.append(graph + (dec,))

