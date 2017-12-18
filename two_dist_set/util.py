from two_dist_set.conference import conference
import numpy as np


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
