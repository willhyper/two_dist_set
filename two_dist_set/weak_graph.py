__author__ = 'chaoweichen'
import numpy as np
import itertools

def generate(srg):
    # A = ((1, 1, 1, 1, 0, 0, 0, 0),    <= 8 = 9 - 1 = v - 1
    #         (0, 0, 0, 1, 1, 1, 0),
    #            (1, 1, 1, 0, 0, 0),)   <= 6 = 9 - 3 = v - len(As) = col
    #             ^
    #      used = 2
    #                ^  ^  ^  ^  ^
    #      cumsum = 10  6  4  4  0      <=len(cumsum) = 5 = 6 - 1 = col - 1

    dec = srg._encoded[srg.state - 1]
    used = 0
    while dec > 0:
        used += dec % 2
        dec >>= 1

    remain = srg.k - used

    if remain < 0:
        return

    unknown_len = srg.v - 1 - srg.state  # 9 - 1 - 3 = 5
    cumsum = srg._encoded[-unknown_len:]

    for indices in itertools.combinations(range(unknown_len), remain):
        for i in indices:
            if i == 0:
                continue
            # elif cumsum[i] +1 > cumsum[i-1] + (1 if i-1 in indices else 0):
            elif cumsum[i] > (cumsum[i - 1] if i - 1 in indices else cumsum[i - 1] - 1):
                break
        else:
            binn = np.zeros(unknown_len, dtype=np.int)
            for i in indices: binn[i] = 1
            yield binn
