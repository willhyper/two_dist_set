#!python
#cython: language_level=3

import numpy as np
from collections import defaultdict


class Question:
    '''
    given A, b, find x st A @ x = b
    '''

    def __init__(self, A, b):
        R, C = A.shape
        assert R == b.shape[0]

        self.A, self.b = A, b

    def __repr__(self):
        A = f'{self.A}'
        b = f'{self.b}'

        R, C = self.A.shape
        x = '?' * C

        szA = f'_({R}x{C})'
        szb = f'_({R}x{1})'
        szx = f'_({C}x{1})'
        return A + szA + ' @ ' + x + szx + ' = ' + b + szb

    def reduce_zeros_from_b(self):
        zero_rows = self.b == 0

        if not np.any(zero_rows):
            R, C = self.A.shape
            unknown_columns = np.ones(C, dtype=np.bool)
            return self, unknown_columns

        A0 = self.A[zero_rows, :]

        nonzero_rows = np.invert(zero_rows)
        An, bn = self.A[nonzero_rows, :], self.b[nonzero_rows]

        known_columns = np.logical_or.reduce(A0)
        # known_columns are columns in A0 where elements are 1
        # because A0 @ x = 0, the corresponding element in x must be 0. Thus say known

        unknown_columns = np.invert(known_columns)
        An = An[:, unknown_columns]

        return Question(An, bn), unknown_columns

    def reduce_duplicate_columns(self):

        # encoding
        A = self.A
        R, C = A.shape
        vec = np.array([1 << r for r in range(R)], dtype=np.int)
        enc = vec @ A

        enc_stock = defaultdict(int)
        first_unique_locations = []
        for i, e in enumerate(enc):
            if enc_stock[e] == 0:
                first_unique_locations.append(i)
            enc_stock[e] += 1
        enc_bound = enc_stock.values()
        A_reduced = A[:, first_unique_locations]

        q = Question(A_reduced, self.b)

        return q, enc_bound

def binarize(l, unknown_columns, bound, count):
    '''
    for example,
    bound = (3, 4, 4, 2)
    count = (0, 3, 3, 1)

    this means the first bucket (0, 3) has 0 1's, and 3-0=3 0's
    the 2nd bucket (3,4) has 3 1's, and 4-3=1 0's
    the 3rd bucket is sames as the 2nd
    the 4th bucket (1,2) has 1 1's, and 2-1=1 0's.

    so returns [0 0 0 1 1 1 0 1 1 1 0 1 0] = solution_q2
                ^     ^       ^       ^
                1st   2nd     3rd     4th

    solution_q2 is the unknown subset of solution_q1
    the known subset is easy. They are all zeros.
    '''

    solution_q1 = np.zeros(l, dtype=np.int)
    solution_q2 = np.zeros(sum(bound), dtype=np.int)
    ptr = 0
    for c, b in zip(count, bound):
        solution_q2[ptr: ptr + c] = 1
        ptr += b

    solution_q1[unknown_columns] = solution_q2
    return solution_q1
