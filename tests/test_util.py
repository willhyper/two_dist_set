from srg import util
import numpy as np


def test_partition():
    s = 6
    bound = (5, 4)

    expect = [(2, 4), (3, 3), (4, 2), (5, 1)]
    actual = util.partition(s, bound)
    for tuple_a, tuple_b in zip(actual, expect):
        assert np.array_equal(tuple_a, tuple_b)
