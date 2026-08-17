import numpy as np
from srg import unique


def test_reduce_expand_roundtrip():
    A = np.array([[1, 1, 1, 1, 0, 0, 0],
                  [1, 1, 0, 0, 1, 1, 0],
                  [1, 1, 1, 1, 1, 1, 1]], dtype=np.int8)

    A_reduced, bounds, unique_loc = unique.reduce(A)
    assert np.array_equal(bounds, [2, 2, 2, 1])
    assert np.array_equal(unique_loc, [0, 2, 4, 6])

    A_exp = unique.expand(A_reduced, bounds)
    assert np.array_equal(A_exp, A)
