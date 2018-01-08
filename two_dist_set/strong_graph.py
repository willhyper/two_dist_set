__author__ = 'chaoweichen'

import numpy as np
from . import weak_graph
from two_dist_set.srg import SRG
from collections import deque
from types import coroutine


def assert_arg(v: int, k: int, l: int, u: int):
    assert (v - k - 1) * u == k * (k - l - 1), f'{(v,k,l,u)} is not a strongly regular graph problem.'


@coroutine
def filter_coroutine(s: SRG):

    if s.unknown_len_of_current_row == 0:
        return

    M = s.to_matrix_essential()
    ri = s.state

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
            yield s + weak


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
