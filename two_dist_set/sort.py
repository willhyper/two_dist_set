import numpy as np
from collections import deque, namedtuple

SortInstruct = namedtuple('SortInstruct', 'row colrange div_index')


class AdjMat:
    def __init__(self, Mat):
        self.Mat = Mat
        self.v = Mat.shape[0]

    def sort(self):
        first_zero_index = self._sort(0, (1, self.v))
        si = SortInstruct(row=0, colrange=(1, self.v), div_index=first_zero_index)
        q = deque()
        q.append(si)

        while q:
            si = q.popleft()
            sii = self._div_sort(si)
            for e in sii:
                q.append(e)

    def _div_sort(self, si: SortInstruct):
        out = []

        row = si.row
        c0 = si.colrange[0]
        c1 = si.colrange[1]
        di = si.div_index

        c0_new = c0 + 1 if row + 1 == c0 else c0
        si1 = SortInstruct(row=row + 1, colrange=(c0_new, di), div_index=None)
        di1 = self._sort(row=si1.row, colrange=si1.colrange)

        si2 = SortInstruct(row=row + 1, colrange=(di, c1), div_index=None)
        di2 = self._sort(row=si2.row, colrange=si2.colrange)

        if di1:
            si1 = si1._replace(div_index=di1)
            out.append(si1)
        if di2:
            si2 = si2._replace(div_index=di2)
            out.append(si2)

        return out

    def _sort(self, row, colrange):
        if row >= colrange[0]:
            return None
        if colrange[0] >= colrange[1]:
            return None

        M = self.Mat
        a = M[row, colrange[0]:colrange[1]]
        i = np.argsort(-a)  # large element first, so negate a.

        ii = np.arange(self.v)
        ii[colrange[0]: colrange[1]] = i + colrange[0]

        S = M
        S = S[:, ii]
        S = S[ii, :]
        assert np.array_equal(S, S.T)

        self.Mat = S

        # find the first zero index
        s = S[row, colrange[0]:colrange[1]]
        zero_indices = np.where(s == 0)[0]  # where returns a tuple. take the 1st element, which is an array

        first_zero_index = zero_indices[0] + colrange[0] if len(zero_indices) > 0 else None

        return first_zero_index


def sort(A):
    AM = AdjMat(A)
    AM.sort()
    return AM.Mat
