__author__ = 'chaoweichen'
import numpy as np
from . import weak_graph
from collections import deque
from two_dist_set.srg import SRG


def assert_arg(v: int, k: int, l: int, u: int):
    assert (v - k - 1) * u == k * (k - l - 1), f'{(v,k,l,u)} is not a strongly regular graph problem.'


def generate_seed(v: int, k: int, l: int, u: int):
    seed = np.zeros(v - 1, dtype=np.int)
    seed[:k] = 1
    return seed


def assert_strong(mat, v: int, k: int, l: int, u: int):
    assert_arg(v, k, l, u)

    I = np.identity(v, dtype=np.int)
    J = np.ones((v, v), dtype=np.int)
    const = (k - u) * I + u * J
    assert np.array_equal(mat @ mat - (l - u) * mat, const)

    det = np.rint(np.linalg.det(mat))
    assert det == determinant(v, k, l, u)


def conference(v: int, k: int, l: int, u: int):
    return 2 * k + (v - 1) * (l - u)


def eig(v: int, k: int, l: int, u: int):
    conf = conference(v, k, l, u)  # if conference graph, conf == 0, so D becomes non-integer

    D = np.sqrt((l - u) ** 2 + 4 * (k - u))
    D = int(D) if conf != 0 else D

    eig = k, ((l - u) + D) / 2, ((l - u) - D) / 2
    eig = tuple(int(x) if conf != 0 else x for x in eig)  # if not conference graph, eigvalues are integer
    mul = 1, int(((v - 1) - conf / D) / 2), int(((v - 1) + conf / D) / 2)  # multiplicity is always integer

    return tuple(zip(eig, mul))


def determinant(v: int, k: int, l: int, u: int):
    prod = 1
    for e, m in eig(v, k, l, u):
        prod *= e ** m

    return int(round(prod))


def generate(s: SRG):
    q = deque()
    q.append(s)

    while q:
        s = q.pop()

        if s.state == s.v - 1:  # data structure property. when met, graph is complete
            yield s.to_matrix()
        else:
            M = s.to_matrix()
            row = s.state
            unknown_len = s.v - row - 1

            for vec in weak_graph.generate(s):

                for xx in range(row):
                    inprod = s.l if M[xx, row] == 1 else s.u
                    rem = inprod - M[row, 0:row].dot(M[xx, 0:row])
                    if vec.dot(M[xx, -unknown_len:]) != rem:
                        break
                else:
                    cp = s.copy()
                    cp.add(vec)
                    q.append(cp)
