__author__ = 'chaoweichen'
import numpy as np


class SRG:
    def __init__(self, v, k, l, u):
        self.v, self.k, self.l, self.u = v, k, l, u
        self._state = 0
        self._encoded = np.zeros(v - 1, dtype=np.int)

    def add(self, row):
        assert self._state + len(row) == self.v - 1, "length of row mismatches status"

        self._encoded[self._state:] += row
        self._encoded[self._state + 1:] <<= 1
        self._state += 1

    @property
    def state(self):
        return self._state

    def copy(self):
        cp = SRG(self.v, self.k, self.l, self.u)
        cp._encoded = np.copy(self._encoded)
        cp._state = self._state
        return cp

    def __repr__(self):
        return f'SRG({self._state} : {self._encoded})'

    def to_matrix(self):
        cp = self.copy()
        i = cp.state
        mat = np.zeros((self.v, self.v), dtype=np.int)
        while i > 0:
            # decoding
            cp._encoded[i:] >>= 1
            i -= 1
            v = cp._encoded[i:] % 2
            cp._encoded[i:] -= v

            # assign to symmetric matrix
            mat[i, i + 1:] = v
            mat[i + 1:, i] = v

        return mat

