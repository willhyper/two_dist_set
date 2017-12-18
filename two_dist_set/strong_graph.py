__author__ = 'chaoweichen'
import numpy as np
from . import weak_graph
from two_dist_set.srg import SRG
from collections import deque
import multiprocessing


def assert_arg(v: int, k: int, l: int, u: int):
    assert (v - k - 1) * u == k * (k - l - 1), f'{(v,k,l,u)} is not a strongly regular graph problem.'


def generate_seed(v: int, k: int, l: int, u: int):
    first_row = np.zeros(v - 1, dtype=np.int)
    first_row[:k] = 1

    s = SRG(v, k, l, u)
    s.add(first_row)

    second_row = np.zeros(v - 2, dtype=np.int)

    remain_ones_number = k - l - 1
    second_row[:l] = 1
    second_row[k - 1:k + remain_ones_number - 1] = 1

    s.add(second_row)
    return s


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


def strong_generator(s: SRG):
    ri = s.state
    unknown_len = s.v - ri - 1

    if unknown_len == 0:
        return

    M = s.to_matrix_essential()
    M_left, M_ri, M_right = M[:, :ri], M[:, ri], M[:, ri + 1:]

    inner_prod_required = np.array([s.l if M_ri[r] == 1 else s.u for r in range(ri)], dtype=np.int)

    k_used = M_left @ M_ri
    inner_prod_remain = inner_prod_required - k_used

    for vec in weak_graph.generate(s):
        inner_prod_actual = M_right @ vec

        for actual, remain in zip(inner_prod_actual, inner_prod_remain):
            if actual != remain:
                break
        else:
            cp = s.copy()
            cp.add(vec)
            yield cp


def strong_list(s: SRG):
    return list(strong_generator(s))


def generate(s: SRG):
    q = deque()
    q.append(s)

    while q:
        s = q.pop()

        if s.state == s.v - 1:  # data structure property. when met, graph is complete
            yield s.to_matrix()
        else:
            for survivor in strong_generator(s):
                q.append(survivor)