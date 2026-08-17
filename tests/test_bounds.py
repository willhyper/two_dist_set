import numpy as np
from srg import bounds
from srg.model import array


def test_lower_upper_bound():
    A = array([[0, 0, 0, 0, 1],
               [0, 0, 1, 1, 0],
               [1, 0, 1, 0, 0],
               [1, 1, 0, 0, 0]])
    b = array([1, 1, 0, 1])
    bound = array([1, 1, 1, 1, 1])

    bounds.lower_upper_bound(A, b, bound)
    assert np.array_equal(bound, [0, 1, 0, 1, 1])


def test_lower_upper_bound_no_change_when_already_tight():
    A = array([[0, 1], [0, 1], [0, 0], [1, 0], [1, 0], [0, 0]])
    b = array([4, 4, 0, 4, 4, 0])
    bound = array([4, 4])

    bounds.lower_upper_bound(A, b, bound)
    assert np.array_equal(bound, [4, 4])


def test_one_element_row_locs():
    A = array([[0, 0, 0, 0, 1],
               [0, 0, 1, 1, 0],
               [1, 0, 1, 0, 0],
               [1, 1, 0, 0, 0]])

    rcs = bounds.one_element_row_locs(A)
    assert rcs == {(0, 4)}


def test_one_element_row_locs_multiple():
    A = array([[0, 1], [0, 1], [0, 0], [1, 0], [1, 0], [0, 0]])

    rcs = bounds.one_element_row_locs(A)
    assert rcs == {(1, 1), (4, 0)}
