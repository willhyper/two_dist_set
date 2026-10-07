#!python
#cython: language_level=3
import numpy as np

def delete(a: np.array, index, axis: int = 0) -> np.array:
    '''np.delete(a, index, axis) for 1-D/2-D arrays, via a boolean mask: np.delete
    spends most of its time on generic-ndim dispatch, and this is called
    hundreds of thousands of times on tiny arrays.'''
    keep = np.ones(a.shape[axis], dtype=bool)
    keep[index] = False
    return a[:, keep] if axis == 1 else a[keep]


def _pop_col(A: np.array, index: int):
    col = A[:, index]
    A_rest = delete(A, index, axis=1)
    return col, A_rest


def _pop_ele(row: np.array, index: int):
    ele = row[index]
    row_rest = delete(row, index)
    return ele, row_rest


def enum(quota: int, bounds: np.array, loc: int):
    m, bounds_rest = _pop_ele(bounds, loc)

    start_from = max(0, quota - bounds_rest.sum())
    for quota_used in range(start_from, m + 1):  # q = 0,1,2
        quota_rest = quota - quota_used
        yield quota_used, quota_rest
