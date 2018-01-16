from two_dist_set import simplifier, util

__author__ = 'chaoweichen'

from . import weak_graph
from two_dist_set.srg import SRG
from types import coroutine
import numpy as np


@coroutine
def filter_coroutine(s: SRG):
    if s.unknown_len_of_current_row == 0:
        return

    M_right, inner_prod_remain = s.question()

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


def _advance_from_weak(s: SRG):
    fltr = filter_coroutine(s)
    fltr.send(None)  # prime

    for weak in weak_graph.advance(s):
        pass_fail = fltr.send(weak)
        if pass_fail:
            yield s + weak


def advance(s: SRG):
    # yield from _advance_from_weak(s)
    yield from _advance_from_partition(s)


def _advance_from_partition(s: SRG)-> SRG:

    A, b = s.question()
    R, C = A.shape

    if C == 0:
        # yield s
        return

    q1 = simplifier.Question(A, b)

    q2, unknown_columns = q1.reduce_zeros_from_b()


    q2R, q2C = q2.A.shape

    if q2C == 0:
        pivot_vector = np.zeros(C, dtype=np.int)
        yield s + pivot_vector
        return

    q3, enc_bound = q2.reduce_duplicate_columns()

    # enc_smaller_bound = [e for e in enc_bound]
    # for i, be in enumerate(q3.b):
    #     row_i = q3.A[i, :]
    #     for c, value in enumerate(row_i):
    #         if value == 1:
    #             enc_smaller_bound[c] = min(be, enc_smaller_bound[c])
    #
    # enc_smaller_bound = tuple(enc_smaller_bound)
    enc_smaller_bound = enc_bound

    remain = s.k - s.used_k_of_current_row
    candidates = util.partition(remain, enc_smaller_bound)

    for candidate in candidates:
        if np.array_equal(q3.A @ candidate, q3.b):
            binarized = simplifier.binarize(C, unknown_columns, enc_bound, candidate)
            yield s + binarized
