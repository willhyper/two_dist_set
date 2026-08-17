import numpy as np
from srg import gauss_elim
from srg.model import array


def test_elim():
    A = array([[1, 1, 1, 1, 1],
               [1, 1, 0, 0, 0],
               [0, 0, 1, 1, 0],
               [1, 1, 1, 1, 0],
               [1, 0, 1, 0, 1]])
    b = array([5, 2, 2, 4, 3])

    Ae, be = gauss_elim.elim(A, b)

    At = array([[0, 0, 0, 0, 1],
                [0, 0, 1, 1, 0],
                [1, 0, 1, 0, 0],
                [1, 1, 0, 0, 0]])
    bt = array([1, 2, 2, 2])

    assert np.array_equal(Ae, At)
    assert np.array_equal(be, bt)
