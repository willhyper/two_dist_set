__author__ = 'chaoweichen'
import numpy as np
from srg import sorter


def test_9_4_1_2():
    # v, k, l, u = 9, 4, 1, 2

    A = np.array([
        [0, 1, 0, 0, 1, 1, 0, 0, 1],
        [1, 0, 1, 0, 0, 0, 1, 0, 1],
        [0, 1, 0, 1, 1, 0, 1, 0, 0],
        [0, 0, 1, 0, 1, 0, 0, 1, 1],
        [1, 0, 1, 1, 0, 1, 0, 0, 0],
        [1, 0, 0, 0, 1, 0, 1, 1, 0],
        [0, 1, 1, 0, 0, 1, 0, 1, 0],
        [0, 0, 0, 1, 0, 1, 1, 0, 1],
        [1, 1, 0, 1, 0, 0, 0, 1, 0]
    ])

    B = np.array([
        [0, 1, 1, 1, 1, 0, 0, 0, 0],
        [1, 0, 1, 0, 0, 1, 1, 0, 0],
        [1, 1, 0, 0, 0, 0, 0, 1, 1],
        [1, 0, 0, 0, 1, 1, 0, 1, 0],
        [1, 0, 0, 1, 0, 0, 1, 0, 1],
        [0, 1, 0, 1, 0, 0, 1, 1, 0],
        [0, 1, 0, 0, 1, 1, 0, 0, 1],
        [0, 0, 1, 1, 0, 1, 0, 0, 1],
        [0, 0, 1, 0, 1, 0, 1, 1, 0]
    ])

    Amax = sorter.maximize(A)

    assert np.array_equal(Amax, B)


def test_13_6_2_3():
    # v,k,l,u = 13,6,2,3
    A = np.array([[0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1],
                  [1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
                  [0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1],
                  [1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1],
                  [1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0],
                  [0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0],
                  [0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0],
                  [0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0],
                  [0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1],
                  [1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1],
                  [1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0],
                  [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1],
                  [1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0]])

    B = np.array([[0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                  [1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0],
                  [1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0],
                  [1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1],
                  [1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1],
                  [1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1],
                  [1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0],
                  [0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1],
                  [0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0],
                  [0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1],
                  [0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1],
                  [0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0],
                  [0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0]])

    Amax = sorter.maximize(A)

    assert np.array_equal(Amax, B)
