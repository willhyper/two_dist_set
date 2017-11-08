__author__ = 'chaoweichen'

from . import globalz
import numpy as np
import itertools


def _cumsum(As, iteration):
    cumsum = np.zeros(iteration, dtype=np.int)
    row = len(As)
    for digit in range(iteration-1, -1, -1):
        aa, As = zip(*[(a % 2, a >> 1) for a in As])
        cumsum[digit] = sum(e << (row - s) for s, e in enumerate(aa))

    used = sum(a % 2 for a in As)
    return cumsum, used


def generate(As):
    # As = (240, 14, 56)

    # A = ((1, 1, 1, 1, 0, 0, 0, 0),    <= 8 = 9 - 1 = v - 1
    #         (0, 0, 0, 1, 1, 1, 0),
    #            (1, 1, 1, 0, 0, 0),)   <= 6 = 9 - 3 = v - len(As) = col
    #             ^
    #      used = 2
    #                ^  ^  ^  ^  ^
    #      cumsum = 10  6  4  4  0      <=len(cumsum) = 5 = 6 - 1 = col - 1

    v, k, row = globalz.v, globalz.k, len(As)

    cumsum_len = v - len(As) - 1
    cumsum, used = _cumsum(As, cumsum_len) # need a cumsum array whose length is col - 1

    if used > k:
        return

    def is_maintain_reverse_sorted_when_adding_1_at(indices):
        for i in indices:
            if i == 0:
                continue
            # elif cumsum[i] +1 > cumsum[i-1] + (1 if i-1 in indices else 0):
            elif cumsum[i] > (cumsum[i - 1] if i - 1 in indices else cumsum[i - 1] - 1):
                return False

        return True

    for indices in itertools.combinations(range(cumsum_len), k - used):
        if is_maintain_reverse_sorted_when_adding_1_at(indices):
            # if 0, add 16
            # if 1, add 8
            # if 2, add 4
            # if 3, add 2
            # if 4, add 1
            candidate = sum(1 << (cumsum_len - i - 1) for i in indices)
            yield candidate
