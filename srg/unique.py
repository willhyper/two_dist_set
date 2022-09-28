#!python
#cython: language_level=3

import numpy as np


def _encode(A: np.array) -> list:
    '''
    A = np.array([[1, 1, 1, 1, 0, 0, 0],
                  [1, 1, 0, 0, 1, 1, 0],
                  [1, 1, 1, 1, 1, 1, 1]], dtype=np.int8)
    :param A:
    :return: array([7, 7, 5, 5, 3, 3, 1], dtype=int16)
    '''
    R, C = A.shape
    _A = A.astype(np.int)
    _sum = _A[-1, :]
    for r in reversed(range(R - 1)):
        _sum += _A[r, :] << (R - 1 - r)

    return _sum


def reduce(A: np.array):
    enc = _encode(A)  # array([7, 7, 5, 5, 3, 3, 1])
    diff_enc = np.diff(enc)  # array([ 0, -2,  0, -2,  0, -2])
    unique_loc = diff_enc.nonzero()[0] + 1  # array([2, 4, 6])
    unique_loc = np.r_[0, unique_loc]  # 0 is always the first unique loc
    bounds = np.diff(unique_loc)  # array([2, 2, 2])
    bounds = np.r_[bounds, len(enc) - bounds.sum()]  # array([2, 2, 2, 1])

    return A[:, unique_loc], bounds, unique_loc


def expand(A: np.array, bounds: np.array):
    R, C = A.shape

    A_dup = []
    for c, repeat in enumerate(bounds):
        a = A[:, c].reshape(R, 1)
        a_dup = np.repeat(a, repeats=repeat, axis=1)
        A_dup.append(a_dup)

    return np.hstack(A_dup)


if __name__ == '__main__':
    A = np.array([[1, 1, 1, 1, 0, 0, 0],
                  [1, 1, 0, 0, 1, 1, 0],
                  [1, 1, 1, 1, 1, 1, 1]], dtype=np.int8)

    A_reduced, bounds, unique_loc = reduce(A)

    print(A_reduced)
    print('bounds', bounds)
    print('unique_loc', unique_loc)

    A_exp = expand(A_reduced, bounds)

    print(A_exp)
    assert np.array_equal(A_exp, A)
