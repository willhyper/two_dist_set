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

    @property
    def encoded_representation(self):
        return self._encoded

    @property
    def unknown_len_of_current_row(self):
        return self.v - 1 - self._state  # 9 - 1 - 3 = 5

    @property
    def used_k_of_current_row(self):
        dec = self._encoded[self._state - 1]
        used = 0
        while dec > 0:
            used += dec % 2
            dec >>= 1
        return used

    def copy(self):
        cp = SRG(self.v, self.k, self.l, self.u)
        cp._encoded = np.copy(self._encoded)
        cp._state = self._state
        return cp

    def __repr__(self):
        return f'SRG({self._state} : {self._encoded})'

    def to_matrix(self):
        enc = self._encoded.copy()
        i = self.state
        mat = np.zeros((self.v, self.v), dtype=np.int)
        while i > 0:
            # decoding
            enc[i:] >>= 1
            i -= 1
            v = enc[i:] % 2
            enc[i:] -= v

            # assign to symmetric matrix
            mat[i, i + 1:] = v
            mat[i + 1:, i] = v

        return mat

    def to_matrix_essential(self):

        enc = self._encoded.copy()
        R, C, i = self.state, self.v, self.state
        mat = np.zeros((R, C), dtype=np.int)
        while i > 0:
            # decoding
            enc[i:] >>= 1
            i -= 1
            v = enc[i:] % 2
            enc[i:] -= v

            # assign to partial matrix
            mat[i, i + 1:] = v
            mat[i + 1:, i] = v[:R - i - 1]

        return mat

    @classmethod
    def from_matrix(cls, mat, v, k, l, u):
        s = SRG(v, k, l, u)
        row_num = mat.shape[0]
        for i in range(row_num):
            row = mat[i, i+1:]
            s.add(row)

        return s
