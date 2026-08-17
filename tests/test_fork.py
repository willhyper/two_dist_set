import numpy as np
from srg import fork
from srg.model import array


def test_enum_from_zero():
    quota = 4
    bounds = array((2, 2, 2, 1))

    minloc = np.argmin(bounds)
    g = fork.enum(quota, bounds, minloc)
    assert np.array_equal(next(g), [0, 4])
    assert np.array_equal(next(g), [1, 3])


def test_enum_pruned_by_remaining_bounds():
    quota = 3
    bounds = array((1, 1, 1))

    minloc = np.argmin(bounds)
    g = fork.enum(quota, bounds, minloc)
    assert np.array_equal(next(g), [1, 2])
