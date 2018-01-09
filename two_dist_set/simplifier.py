import numpy as np
from scipy import linalg
from collections import defaultdict, deque

from pprint import pprint
import collections

np.set_printoptions(precision=3, suppress=True)


class symbolic_scalar:
    def __init__(self, a):
        assert not isinstance(a, collections.Iterable)
        self.set_value(a)

    @property
    def value(self):
        return self.get_value()

    def get_value(self):
        return self._a[0]

    def set_value(self, a):
        self._a = [a]

    def __repr__(self):
        return f'{self.value}'


ss = symbolic_scalar


class Question:
    '''
    given A, b, find x st A @ x = b
    '''

    unknown = 0 # np.nan

    def __init__(self, A, b, x=None):
        R, C = A.shape
        assert R == b.shape[0]

        self.A, self.b = A, b

        if x is None:
            self.x = [ss(Question.unknown) for _ in range(C)]
        else:
            assert len(x) == C
            self.x = x

    def __repr__(self):
        A = f'{self.A}'
        b = f'{self.b}'

        R, C = self.A.shape
        x = f'{self.x}'

        szA = f'_({R}x{C})'
        szb = f'_({R}x{1})'
        szx = f'_({C}x{1})'
        return A + szA + ' @ ' + x + szx + ' = ' + b + szb

    def reduce_zeros_from_b(self):
        zero_rows = self.b == 0

        if not np.any(zero_rows):
            return self

        A0 = self.A[zero_rows, :]

        nonzero_rows = np.invert(zero_rows)
        An, bn = self.A[nonzero_rows, :], self.b[nonzero_rows]

        nonzero_columns = np.logical_or.reduce(A0) #  nonzero_columns in A0 results in 0 element in x st A0 @ x = 0
        zero_columns = np.invert(nonzero_columns)
        An = An[:, zero_columns]

        x_remain = []
        for i in range(A0.shape[1]):
            if i in nonzero_columns.nonzero()[0]:  # [0] is to unpack a tuple:
                self.x[i].set_value(0)
            else:
                x_remain.append(self.x[i])

        return Question(An, bn, x_remain)

    def reduce_duplicate_columns(self):

        # encoding
        A = self.A
        R, C = A.shape
        vec = np.array([1 << r for r in range(R)], dtype=np.int)
        enc = vec @ A

        enc_stock = defaultdict(deque)
        for i, e in enumerate(enc):
            enc_stock[e].append(i)

        li0 = [li[0] for li in enc_stock.values()]  # list of indices of first unique encode
        A_reduced = A[:, li0]
        enc_reduced = enc[li0]  # = d.keys()

        # x_remain = [self.x[i] for i in li0]
        q = Question(A_reduced, self.b)#, x_remain)

        return q, enc_reduced, enc_stock

    def solvable(self):
        Ab = np.hstack((self.A, self.b.reshape(-1, 1)))
        rank_Ab = np.linalg.matrix_rank(Ab)
        rang_A = np.linalg.matrix_rank(self.A)

        return rank_Ab == rang_A

    def qr_decomposition(self):
        Q, R = linalg.qr(self.A, mode='economic')
        return Question(R, Q.T @ self.b, self.x)

    def solve(self):
        x, residues, effective_ranks, sv = linalg.lstsq(self.A, self.b)

        x = np.round(x) # special to SRG
        x = x.astype(np.int)# special to SRG

        if not np.allclose(self.A @ x, self.b):
            print(self)
            pprint(self.A)
            pprint(x)
            pprint(self.b)

            print('residue', residues)
            print('effective ranks', effective_ranks)
            print('sv', sv)

            assert False, "Oops.................."

        for sol, v in zip(self.x, x):
            sol.set_value(v)

    def get_solution_copy(self):
        return [e.get_value() for e in self.x]

