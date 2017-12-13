__author__ = 'chaoweichen'

from two_dist_set.srg import SRG
import numpy as np
import itertools


def generate(s: SRG):
    # A = ((1, 1, 1, 1, 0, 0, 0, 0),    <= 8 = 9 - 1 = v - 1
    #         (0, 0, 0, 1, 1, 1, 0),
    #            (1, 1, 1, 0, 0, 0),)   <= 6 = 9 - 3 = v - len(As) = col
    #             ^
    #      used = 2
    #                ^  ^  ^  ^  ^
    #      cumsum = 10  6  4  4  0      <=len(cumsum) = 5 = 6 - 1 = col - 1

    dec = s._encoded[s.state - 1]
    used = 0
    while dec > 0:
        used += dec % 2
        dec >>= 1

    remain = s.k - used

    if remain < 0:
        return

    unknown_len = s.v - 1 - s.state  # 9 - 1 - 3 = 5
    unknown = s._encoded[-unknown_len:]

    for indices in itertools.combinations(range(unknown_len), remain):
        for i in indices:
            if i == 0:
                continue
            # elif unknown[i] +1 > unknown[i-1] + (1 if i-1 in indices else 0):
            elif unknown[i] > (unknown[i - 1] if i - 1 in indices else unknown[i - 1] - 1):
                break
        else:
            binn = np.zeros(unknown_len, dtype=np.int)
            for i in indices: binn[i] = 1
            yield binn
