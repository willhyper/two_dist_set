from two_dist_set import representation
import numpy as np

def test_from_vec_to_scalar():
    A = ((1, 1, 1, 1, 0, 0, 0, 0),
         (0, 0, 0, 1, 1, 1, 0),
         (1, 1, 1, 0, 0, 0),)
    B = (240, 14, 56)

    S = representation.from_vectors(A, 9, 4, 1, 2).to_scalars()

    for s, b in zip(S, B):
        assert s == b


def test_from_scalars_to_vec():
    A = ((1, 1, 1, 1, 0, 0, 0, 0),
         (0, 0, 0, 1, 1, 1, 0),
         (1, 1, 1, 0, 0, 0),)
    B = (240, 14, 56)

    V = representation.from_scalars(B, 9, 4, 1, 2).to_vectors()

    for v, a in zip(V, A):
        assert v == a


def test_to_matrix():
    A = ((1, 1, 1, 1, 0, 0, 0, 0),
         (0, 0, 0, 1, 1, 1, 0),
         (1, 1, 1, 0, 0, 0),)

    Amat = representation.from_vectors(A, 9, 4, 1, 2).to_matrix()
    ans = [[0, 1, 1, 1, 1, 0, 0, 0, 0],
           [1, 0, 0, 0, 0, 1, 1, 1, 0],
           [1, 0, 0, 1, 1, 1, 0, 0, 0],
           [1, 0, 1, 0, 0, 0, 0, 0, 0]]

    assert np.array_equal(Amat, ans)


def test_to_matrix2():
    v, k, l, u = 9, 4, 1, 2
    A = tuple(1 if i < k else 0 for i in range(v - 1))
    A = (A,)  # tuple in a tuple

    Amat = representation.from_vectors(A, v, k, l, u).to_matrix()

    ans = np.array([[0, 1, 1, 1, 1, 0, 0, 0, 0],
                    [1, 0, 0, 0, 0, 0, 0, 0, 0]], dtype=np.int)

    assert np.array_equal(Amat, ans)

