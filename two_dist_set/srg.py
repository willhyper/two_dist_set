__author__ = 'chaoweichen'
import numpy as np


class SRG:
    def __init__(self, v, k, l, u):
        self.v, self.k, self.l, self.u = v, k, l, u
        self._ri = 0
        self._encoded = np.zeros(v - 1, dtype=np.int)

    def __add__(self, row):
        l = self.v - 1 - self._ri
        assert len(row) == l, f"expect len(row)=={l} but got len({row})={len(row)}"

        cp = self.copy()
        cp._encoded[cp._ri:] += row
        cp._encoded[cp._ri + 1:] <<= 1
        cp._ri += 1

        return cp


    def __sub__(self, other):

        ri = self._ri
        assert ri == other._ri + 1, "only allow subtraction between adjacent state"

        this = self._encoded.copy()# [ri + 1:] >> 1
        that = other._encoded.copy()

        this[ri:] >>= 1
        this = this[ri-1:]
        that = that[ri-1:]

        return this - that

    def __eq__(self, other):
        v = self.v == other.v
        k = self.k == other.k
        l = self.l == other.l
        u = self.u == other.u

        ri = self._ri == other._ri

        enc = np.array_equal(self._encoded, other._encoded)

        return ri and enc and v and k and l and u

    @property
    def state(self):
        return self._ri

    @property
    def encoded_representation(self):
        return self._encoded

    @property
    def unknown_len_of_current_row(self):
        return self.v - 1 - self._ri  # 9 - 1 - 3 = 5 # 1 is the '0' is the diagonal

    @property
    def used_k_of_current_row(self):
        dec = self._encoded[self._ri - 1]
        used = 0
        while dec > 0:
            used += dec % 2
            dec >>= 1
        return used # = sum(self.known_partial_vector_of_current_row)

    @property
    def known_partial_vector_of_current_row(self):
        vec = np.zeros(self._ri, dtype=np.int)
        ri = self._ri - 1
        dec = self._encoded[ri]
        while dec > 0:
            vec[ri] = dec % 2
            dec >>= 1
            ri -= 1
        return vec

    def copy(self):
        cp = SRG(self.v, self.k, self.l, self.u)
        cp._encoded = np.copy(self._encoded)
        cp._ri = self._ri
        return cp

    def __repr__(self):

        # construct a string representing the known part of the matrix
        mat = self.to_matrix_essential()
        strr = ''
        R, C = mat.shape
        for r in range(R):
            row = mat[r, :]
            strr += str(row)[1:-1] + '\n'
        strr = strr[:-1]  # remove the trailing \n
        strr = strr.replace(' ', '')

        current_known_partial_vec_str = str(self.known_partial_vector_of_current_row)[1:-1].replace(' ', '')

        question = '?' * self.unknown_len_of_current_row


        out = f'(v, k, l, u) = {self.v, self.k, self.l, self.u}\n'

        out += strr + '\n'
        out += current_known_partial_vec_str + '0' + question

        out += f'\nSRG({self._ri} : {self._encoded})'

        return out

    def to_matrix(self):
        enc = self._encoded.copy()
        i = self._ri
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
        R, C, i = self._ri, self.v, self._ri
        mat = SRG._decode(enc, R, C, i)

        return mat

    @classmethod
    def _decode(cls, enc, R, C, i):

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
            s += row

        return s
