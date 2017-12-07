__author__ = 'chaoweichen'
from collections import deque

import numpy as np
import itertools
from . import representation


def _cumsum(As, iteration):
    cumsum = np.zeros(iteration, dtype=np.int)
    row = len(As)
    for digit in range(iteration - 1, -1, -1):
        aa, As = zip(*[(a % 2, a >> 1) for a in As])
        cumsum[digit] = sum(e << (row - s) for s, e in enumerate(aa))

    used = sum(a % 2 for a in As)
    return cumsum, used

def generate(As, v, k):
    # As = (240, 14, 56)

    # A = ((1, 1, 1, 1, 0, 0, 0, 0),    <= 8 = 9 - 1 = v - 1
    #         (0, 0, 0, 1, 1, 1, 0),
    #            (1, 1, 1, 0, 0, 0),)   <= 6 = 9 - 3 = v - len(As) = col
    #             ^
    #      used = 2
    #                ^  ^  ^  ^  ^
    #      cumsum = 10  6  4  4  0      <=len(cumsum) = 5 = 6 - 1 = col - 1

    cumsum_len = v - len(As) - 1
    cumsum, used = _cumsum(As, cumsum_len)  # need a cumsum array whose length is col - 1
    remain = k - used

    if remain < 0:
        return

    for indices in itertools.combinations(range(cumsum_len), remain):
        for i in indices:
            if i == 0:
                continue
            # elif cumsum[i] +1 > cumsum[i-1] + (1 if i-1 in indices else 0):
            elif cumsum[i] > (cumsum[i - 1] if i - 1 in indices else cumsum[i - 1] - 1):
                break
        else:
            yield representation.ind2dec(indices, cumsum_len)
