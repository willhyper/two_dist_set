#!python
#cython: language_level=3
import numpy as np
from . import srg

def _pop_col(A: np.array, index: int):
    col = A[:, index]
    A_rest = np.delete(A, index, axis=1)
    return col, A_rest


def _pop_ele(row: np.array, index: int):
    ele = row[index]
    row_rest = np.delete(row, index)
    return ele, row_rest


def enum(quota: int, bounds: np.array, loc: int):
    m, bounds_rest = _pop_ele(bounds, loc)

    start_from = max(0, quota - bounds_rest.sum())
    for quota_used in range(start_from, m + 1):  # q = 0,1,2
        quota_rest = quota - quota_used
        yield quota_used, quota_rest


if __name__ == '__main__':
    # test 1
    quota = 4
    bounds = srg.array((2, 2, 2, 1))

    minloc = np.argmin(bounds)
    g = enum(quota, bounds, minloc)
    assert np.array_equal(next(g), [0, 4])
    assert np.array_equal(next(g), [1, 3])

    # test 2
    quota = 3
    bounds = srg.array((1, 1, 1))

    minloc = np.argmin(bounds)
    g = enum(quota, bounds, minloc)
    assert np.array_equal(next(g), [1, 2])
