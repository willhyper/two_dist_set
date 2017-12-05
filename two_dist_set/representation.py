__author__ = 'chaoweichen'
import numpy as np

class dec2bin:
    @staticmethod
    def encode(n, digit):
        ans = []
        while digit > 0:
            i = n%2
            ans.append(i)
            n >>= 1
            digit -= 1

        return tuple(reversed(ans))

    @staticmethod
    def decode(m):
        l = len(m)
        s = 0
        p = 1 << l
        for d in m:
            p >>= 1
            s += p if d else 0
        return s


class SRG:
    def __init__(self, num, v, m, l, u):
        self.data = tuple(num)
        self.v = v
        self.m = m
        self.l = l
        self.u = u

    def to_scalars(self):
        return self.data

    def to_vectors(self):
        out = ()
        for i, n in enumerate(self.data, start=1):
            e = dec2bin.encode(n, digit=self.v-i)
            out +=(e,)

        return out

    def to_matrix(self):
        A = self.to_vectors()
        row = len(A) + 1
        col = len(A[0]) + 1
        to_construct = np.zeros((row, col), dtype=np.int)
        for r, a in enumerate(A):
            to_construct[r, 1 + r:col] = a

        for d in range(row - 1):
            to_construct[d + 1:row, d] = to_construct[d, d + 1:row]

        return to_construct


def from_vectors(A, v, m, l, u):
    out = ()
    for a in A:
        aa = np.array(a, dtype=np.int)
        n = aa.shape[-1]
        p = 1 << np.arange(n - 1, -1, -1)
        out += (aa.dot(p),)

    return SRG(out, v, m, l, u)


def from_scalars(tuple_of_num, v, m, l, u):
    return SRG(tuple_of_num, v, m, l, u)

def from_matrix(M, v, m, l, u):
    out = []
    for i, row in enumerate(M):
        vec = row[i+1:]
        val = np.polyval(vec, 2)
        out.append(val)
    out = out[:-1]
    return SRG(out, v, m, l, u)

# [1 1 1 1 1 1 0 0 0 0 0 0] 4032
# [1 1 0 0 0 1 1 1 0 0 0] 1592
# [0 1 0 0 1 0 0 1 1 0] 294
# [0 1 0 0 1 0 1 0 1] 149
# [0 1 0 0 1 1 0 1] 77
# [1 1 0 0 0 1 1] 99
# [0 1 1 0 1 0] 26
# [0 1 0 1 1] 11
# [1 1 1 0] 14
# [0 0 1] 1
# [1 1] 3
# [0] 0
# [] 0
