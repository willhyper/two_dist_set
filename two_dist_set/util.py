from two_dist_set.conference import conference
import numpy as np

from two_dist_set.srg import SRG


def eig(v: int, k: int, l: int, u: int):
    conf = conference(v, k, l, u)  # if conference graph, conf == 0, so D becomes non-integer

    D = np.sqrt((l - u) ** 2 + 4 * (k - u))
    D = int(D) if conf != 0 else D

    eig = k, ((l - u) + D) / 2, ((l - u) - D) / 2
    eig = tuple(int(x) if conf != 0 else x for x in eig)  # if not conference graph, eigvalues are integer
    mul = 1, int(((v - 1) - conf / D) / 2), int(((v - 1) + conf / D) / 2)  # multiplicity is always integer

    return tuple(zip(eig, mul))


def determinant(v: int, k: int, l: int, u: int):
    prod = 1
    for e, m in eig(v, k, l, u):
        prod *= e ** m

    return int(round(prod))


def generate_seed(v: int, k: int, l: int, u: int):
    first_row = np.zeros(v - 1, dtype=np.int)
    first_row[:k] = 1

    s = SRG(v, k, l, u)
    s.add(first_row)

    second_row = np.zeros(v - 2, dtype=np.int)

    remain_ones_number = k - l - 1
    second_row[:l] = 1
    second_row[k - 1:k + remain_ones_number - 1] = 1

    s.add(second_row)
    return s


def partition(s: int, bounds: tuple) -> tuple:
    assert s >= 0, "sum to be placed is required >= 0"

    l = len(bounds)
    assert l >= 1, "len(dict) is required >= 1"

    bound, *others = bounds

    if l > 1:

        for v in range(min(bound, s) + 1):
            rem = s - v

            for t in partition(rem, others):
                yield (v,) + t

    else:
        if s <= bound:
            yield (s,)
