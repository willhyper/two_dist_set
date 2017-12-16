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
    #      enc    = 10  6  4  4  0         <=len(enc) = 5 = 6 - 1 = col - 1

    dec = s._encoded[s.state - 1]
    used = 0
    while dec > 0:
        used += dec % 2
        dec >>= 1

    remain = s.k - used
    unknown_len = s.v - 1 - s.state  # 9 - 1 - 3 = 5
    enc = s._encoded[-unknown_len:]

    for indices in itertools.combinations(range(unknown_len), remain):
        start_index = 1 if 0 in indices else 0 # 0 appears up to once. if appearing, it is always at index 0
        for i in indices[start_index:]:
            # enc[i] +1 > enc[i-1] + (1 if i-1 in indices else 0):
            if enc[i] > (enc[i - 1] if i - 1 in indices else enc[i - 1] - 1):
                break
        else:
            binn = np.zeros(unknown_len, dtype=np.int)
            for i in indices: binn[i] = 1 # indices could be[()]
            yield binn
