import numpy as np

from two_dist_set.srg import SRG


def test_9_4_1_2():
    v, k, l, u = 9, 4, 1, 2

    A = np.array([[0, 1, 1, 1, 1, 0, 0, 0, 0],
                  [1, 0, 1, 0, 0, 1, 1, 0, 0],
                  [1, 1, 0, 0, 0, 0, 0, 1, 1],
                  [1, 0, 0, 0, 1, 1, 0, 1, 0],
                  [1, 0, 0, 1, 0, 0, 1, 0, 1],
                  [0, 1, 0, 1, 0, 0, 1, 1, 0],
                  [0, 1, 0, 0, 1, 1, 0, 0, 1],
                  [0, 0, 1, 1, 0, 1, 0, 0, 1],
                  [0, 0, 1, 0, 1, 0, 1, 1, 0]], dtype=np.int)

    s = SRG(v, k, l, u)
    i = s.state

    while i < v - 1:
        r = A[i, i + 1:]

        s.add(r)
        print(s)

        i += 1

    B = s.to_matrix()
    assert np.array_equal(A, B)
