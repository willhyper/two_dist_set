__author__ = 'chaoweichen'
from collections import deque

import numpy as np
import itertools


def generate(A, v, k, l, u):
    q = deque()
    q.append(A)

    while q:
        simple_sym_graph = q.pop()
        if len(simple_sym_graph) == v - 1:  # data structure property. when met, graph is complete
            # print(len(q), simple_sym_graph)
            yield simple_sym_graph  # weak
        else:
            weak_candidates = sorted(_satisfy_weak_condition(simple_sym_graph, v, k, l, u))
            for c in weak_candidates:
                q.append(simple_sym_graph + (c,))


def _cumsum(As, iteration):
    cumsum = np.zeros(iteration, dtype=np.int)
    row = len(As)
    for digit in range(iteration - 1, -1, -1):
        aa, As = zip(*[(a % 2, a >> 1) for a in As])
        cumsum[digit] = sum(e << (row - s) for s, e in enumerate(aa))

    return cumsum


def _satisfy_weak_condition(As, v, k, l, u):
    # As = (240, 14, 56)

    # A = ((1, 1, 1, 1, 0, 0, 0, 0),    <= 8 = 9 - 1 = v - 1
    #         (0, 0, 0, 1, 1, 1, 0),
    #            (1, 1, 1, 0, 0, 0),)   <= 6 = 9 - 3 = v - len(As) = col
    #             ^
    #      used = 2
    #                ^  ^  ^  ^  ^
    #      cumsum = 10  6  4  4  0      <=len(cumsum) = 5 = 6 - 1 = col - 1

    used = sum(a % 2 for a in As)
    remain = k - used
    if remain < 0:
        return  # run out of quota

    cumsum_len = v - len(As) - 1
    cumsum = _cumsum(As, cumsum_len)  # need a cumsum array whose length is col - 1

    for indices in itertools.combinations(range(cumsum_len), remain):
        for i in indices:
            if i == 0:
                continue
            # elif cumsum[i] +1 > cumsum[i-1] + (1 if i-1 in indices else 0):
            elif cumsum[i] > (cumsum[i - 1] if i - 1 in indices else cumsum[i - 1] - 1):
                break
        else:
            # if 0, add 16
            # if 1, add 8
            # if 2, add 4
            # if 3, add 2
            # if 4, add 1
            candidate = sum(1 << (cumsum_len - i - 1) for i in indices)
            yield candidate
