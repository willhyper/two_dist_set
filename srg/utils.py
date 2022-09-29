#!python
#cython: language_level=3

from .srg import Question
from . import pprint
import numpy as np

def eig(v: int, k: int, l: int, u: int):
    conf = conference(v, k, l, u)  # if conference graph, conf == 0, so D becomes non-integer

    D = np.sqrt((l - u) ** 2 + 4 * (k - u))
    D = int(D) if conf != 0 else D

    eig = k, ((l - u) + D) / 2, ((l - u) - D) / 2
    eig = tuple(int(x) if conf != 0 else x for x in eig)  # if not conference graph, eigvalues are integer
    mul = 1, int(((v - 1) - conf / D) / 2), int(((v - 1) + conf / D) / 2)  # multiplicity is always integer

    return tuple(zip(eig, mul))

def conference(v: int, k: int, l: int, u: int):
    return 2 * k + (v - 1) * (l - u)

def determinant(v: int, k: int, l: int, u: int):
    prod = 1
    for e, m in eig(v, k, l, u):
        prod *= e ** m

    return int(round(prod))

def assert_srg(v: int, k: int, l: int, u: int):
    assert (v - k - 1) * u == k * (k - l - 1), f'{(v,k,l,u)} is not a strongly regular graph problem.'

def complement(v: int, k: int, l: int, u: int):
    return v, v - k -1, v -2-2*k +u ,v -2*k +l

def debug(func):

    def wrapper(Q:Question):
        Q_before = Q.copy()

        result = func(Q)
        if Q == Q_before:
            pprint.blue(f'performing {func.__name__}. No change')
        else:
            print(Q_before)
            pprint.green(f'performing {func.__name__}. reduce to')
            print(Q)


        try:
            Q._invariant_check()
        except AssertionError as e:

            print(Q_before)
            pprint.red(f'performing {func.__name__}. AssertionError!')
            print(Q)

            print()

            raise e

        return result

    return wrapper if __debug__ else func

