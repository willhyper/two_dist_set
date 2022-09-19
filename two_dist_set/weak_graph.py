#!python
#cython: language_level=3

from types import coroutine

from two_dist_set.srg import SRG
import numpy as np
import itertools


@coroutine
def filter_coroutine(s: SRG):
    # A = ((1, 1, 1, 1, 0, 0, 0, 0),    <= 8 = 9 - 1 = v - 1
    #         (0, 0, 0, 1, 1, 1, 0),
    #            (1, 1, 1, 0, 0, 0),)   <= 6 = 9 - 3 = v - len(As) = col
    #             ^
    #      used = 2
    #                ^  ^  ^  ^  ^
    #      enc    = 10  6  4  4  0         <=len(enc) = 5 = 6 - 1 = col - 1
    enc = s.encoded_representation[-s.len_pivot_vec:]

    pass_fail = None
    while True:
        indices = yield pass_fail

        pass_fail = False
        start_index = 1 if 0 in indices else 0  # 0 appears up to once. if appearing, it is always at index 0
        for i in indices[start_index:]:
            # enc[i] +1 > enc[i-1] + (1 if i-1 in indices else 0):
            if enc[i] > (enc[i - 1] if i - 1 in indices else enc[i - 1] - 1):
                break
        else:
            pass_fail = True


def generator(s: SRG):

    remain = s.k - s.used_k_of_current_row

    for indices in itertools.combinations(range(s.len_pivot_vec), remain):
        yield indices


def advance(s: SRG):

    unknown_len = s.len_pivot_vec

    fltr = filter_coroutine(s)
    fltr.send(None)

    for indices in generator(s):
        pass_fail = fltr.send(indices)
        if pass_fail:
            binn = np.zeros(unknown_len, dtype=int)
            for i in indices: binn[i] = 1  # indices could be[()]. therefore for loop being skipped
            yield binn
