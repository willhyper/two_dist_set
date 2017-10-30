__author__ = 'chaoweichen'
import numpy as np


class SRG:

    def __init__(self, tuple_of_num):
        self.data = tuple_of_num

        first = tuple_of_num[0]
        v = 1
        while first>0:
            first >>= 1
            v+=1
        self.v = v

    def to_scalars(self):
        return self.data

    def to_vectors(self):
        out = ()
        for i, n in enumerate(self.data, start=1):
            s = np.binary_repr(n, width=self.v-i)
            t = tuple(int(c) for c in s)
            out += (t,)

        return out


    def to_matrix(self):
        A = self.to_vectors()
        row = len(A) + 1
        col = len(A[0]) + 1
        to_construct = np.zeros((row, col), dtype=np.int)
        for r, a in enumerate(A):
            to_construct[r, 1 + r:col] = a

        for d in range(row - 1):  # d=0, 1
            to_construct[d + 1:row, d] = to_construct[d, d + 1:row]

        return to_construct

def from_vectors(A):
    out = ()
    for a in A:
        aa = np.array(a, dtype=np.int)
        n = aa.shape[-1]
        p = 1 << np.arange(n-1, -1, -1)
        out += (aa.dot(p),)

    return SRG(out)

def from_scalars(tuple_of_num):
    return SRG(tuple_of_num)

def test_from_vec_to_scalar():
    A = ((1, 1, 1, 1, 0, 0, 0, 0),
            (0, 0, 0, 1, 1, 1, 0),
               (1, 1, 1, 0, 0, 0),)
    B = (240, 14, 56)

    S = from_vectors(A).to_scalars()

    for s, b in zip(S, B):
        assert s == b

def test_from_scalars_to_vec():
    A = ((1, 1, 1, 1, 0, 0, 0, 0),
            (0, 0, 0, 1, 1, 1, 0),
               (1, 1, 1, 0, 0, 0),)
    B = (240, 14, 56)

    V = from_scalars(B).to_vectors()

    for v, a in zip(V, A):
        assert v == a

def test_to_matrix():
    A = ((1, 1, 1, 1, 0, 0, 0, 0),
            (0, 0, 0, 1, 1, 1, 0),
               (1, 1, 1, 0, 0, 0),)

    Amat = from_vectors(A).to_matrix()
    ans =[[0, 1, 1, 1, 1, 0, 0, 0, 0],
          [1, 0, 0, 0, 0, 1, 1, 1, 0],
          [1, 0, 0, 1, 1, 1, 0, 0, 0],
          [1, 0, 1, 0, 0, 0, 0, 0, 0]]

    assert np.array_equal(Amat, ans)

def test_to_matrix2():
    v, k = 9, 4
    A = tuple(1 if i < k else 0 for i in range(v-1))
    A = (A,) # tuple in a tuple

    Amat = from_vectors(A).to_matrix()

    ans = np.array([[0, 1, 1, 1, 1, 0, 0, 0, 0],
                   [1, 0, 0, 0, 0, 0, 0, 0, 0]], dtype=np.int)

    assert np.array_equal(Amat, ans)


if __name__ == '__main__':

    test_from_vec_to_scalar()
    test_from_scalars_to_vec()
    test_to_matrix()
    test_to_matrix2()
    pass