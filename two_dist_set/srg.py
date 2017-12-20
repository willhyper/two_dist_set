__author__ = 'chaoweichen'
import numpy as np


class SRG:
    def __init__(self, v, k, l, u):
        self.v, self.k, self.l, self.u = v, k, l, u
        self._ri = 0
        self._encoded = np.zeros(v - 1, dtype=np.int)

    def add(self, row):
        assert self._ri + len(row) == self.v - 1, "length of row mismatches status"

        self._encoded[self._ri:] += row
        self._encoded[self._ri + 1:] <<= 1
        self._ri += 1

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
        dec = self._encoded[self._ri - 1]
        decoded = list()
        while dec > 0:
            e = dec % 2
            dec >>= 1
            decoded.append(e)
        return np.array(decoded[::-1], dtype=np.int)

    def known_inner_prod_with_row(self, row):
        mat = self.to_matrix_essential()
        vec = mat[row, : self._ri]
        known = self.known_partial_vector_of_current_row
        return vec.dot(known)

    def copy(self):
        cp = SRG(self.v, self.k, self.l, self.u)
        cp._encoded = np.copy(self._encoded)
        cp._ri = self._ri
        return cp

    def __repr__(self):
        return f'SRG({self._ri} : {self._encoded})'

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
            s.add(row)

        return s

    def current_question(self):

        print(f'(v, k, l, u) = {self.v, self.k, self.l, self.u}')

        # construct a string representing the known part of the matrix
        mat = self.to_matrix_essential()
        strr = ''
        R, C = mat.shape
        for r in range(R):
            row = mat[r,:]
            strr += str(row)[1:-1] + '\n'
        strr = strr[:-1] # remove the trailing \n
        strr = strr.replace(' ', '')

        current_known_partial_vec_str = str(self.known_partial_vector_of_current_row)[1:-1].replace(' ', '')

        question = '?' * self.unknown_len_of_current_row

        print(strr)
        print(current_known_partial_vec_str + '0' + question)
