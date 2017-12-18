__author__ = 'chaoweichen'

from two_dist_set.util import determinant

import numpy as np
from . import weak_graph
from two_dist_set.srg import SRG
from collections import deque
from types import coroutine


def assert_arg(v: int, k: int, l: int, u: int):
    assert (v - k - 1) * u == k * (k - l - 1), f'{(v,k,l,u)} is not a strongly regular graph problem.'


def assert_strong(mat, v: int, k: int, l: int, u: int):
    assert_arg(v, k, l, u)

    I = np.identity(v, dtype=np.int)
    J = np.ones((v, v), dtype=np.int)
    const = (k - u) * I + u * J
    assert np.array_equal(mat @ mat - (l - u) * mat, const)

    det = np.rint(np.linalg.det(mat))
    assert det == determinant(v, k, l, u)


@coroutine
def filter_coroutine(s: SRG):
    ri = s.state
    unknown_len = s.v - ri - 1

    if unknown_len == 0:
        return

    M = s.to_matrix_essential()
    M_left, M_ri, M_right = M[:, :ri], M[:, ri], M[:, ri + 1:]

    inner_prod_required = np.array([s.l if M_ri[r] == 1 else s.u for r in range(ri)], dtype=np.int)

    k_used = M_left @ M_ri
    inner_prod_remain = inner_prod_required - k_used

    pass_fail = None
    while True:
        vec = yield pass_fail
        pass_fail = False

        inner_prod_actual = M_right @ vec

        for actual, remain in zip(inner_prod_actual, inner_prod_remain):
            if actual != remain:
                break
        else:
            pass_fail = True


def strong_generator(s: SRG):
    fltr = filter_coroutine(s)
    fltr.send(None)  # prime

    for weak in weak_graph.generate(s):
        pass_fail = fltr.send(weak)
        if pass_fail:
            cp = s.copy()
            cp.add(weak)
            yield cp


def generate(s: SRG):
    q = deque()
    q.append(s)

    while q:
        s = q.pop()

        if s.state == s.v - 1:  # data structure property. when met, graph is complete
            yield s.to_matrix()
        else:
            for strong in strong_generator(s):
                q.append(strong)
