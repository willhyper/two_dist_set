#!python
#cython: language_level=3

__author__ = 'chaoweichen'
from two_dist_set import simplifier
from two_dist_set import util
from two_dist_set.srg import SRG
import numpy as np
from collections import deque

def _advance_from_partition(s: SRG) -> SRG:
    A, b = s.question()
    R, C = A.shape

    if C == 0:
        # yield s
        return

    q1 = simplifier.Question(A, b)

    q2, unknown_columns = q1.reduce_zeros_from_b()

    q2R, q2C = q2.A.shape

    if q2C == 0:
        pivot_vector = np.zeros(C, dtype=int)
        yield s + pivot_vector
        return

    q3, enc_bound = q2.reduce_duplicate_columns()

    enc_smaller_bound = []
    for column, bound in enumerate(enc_bound):
        q3a = q3.A[:, column]
        b_of_interest = q3.b[q3a==1]
        smaller_bound = min(bound, b_of_interest.min()) if b_of_interest.size > 0 else bound
        enc_smaller_bound.append(smaller_bound)
    enc_smaller_bound = tuple(enc_smaller_bound)

    remain = s.k - s.used_k_of_current_row
    candidates = util.partition(remain, enc_smaller_bound)

    for candidate in candidates:
        if np.array_equal(q3.A @ candidate, q3.b):
            binarized = simplifier.binarize(C, unknown_columns, enc_bound, candidate)
            yield s + binarized


def advance(s: SRG, approach=_advance_from_partition) -> list:
    # yield from approach(s)
    return list(approach(s)) # to be serializable for use multipleprocess

def solve(s: SRG) -> SRG:
    q = deque()
    q.append(s)
    while q:
        s = q.pop()

        if s.state == s.v - 1:  # data structure property. when met, graph is complete
            yield s
        else:
            q += advance(s)