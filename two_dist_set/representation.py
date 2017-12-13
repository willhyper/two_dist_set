__author__ = 'chaoweichen'
import numpy as np


def ind2bin(ind, digit):
    return tuple(1 if i in ind else 0 for i in range(digit))


def ind2dec(ind, digit):
    # if ind includes 0, add 16
    # if ind includes 1, add 8
    # if ind includes 2, add 4
    # if ind includes 3, add 2
    # if ind includes 4, add 1
    return sum(1 << (digit - i - 1) for i in ind)


def dec2bin(n, digit):
    ans = []
    while digit > 0:
        i = n % 2
        ans.append(i)
        n >>= 1
        digit -= 1

    return tuple(reversed(ans))


def bin2dec(m):
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
            e = dec2bin(n, digit=self.v - i)
            out += (e,)

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
        vec = row[i + 1:]
        val = np.polyval(vec, 2)
        out.append(val)
    out = out[:-1]
    return SRG(out, v, m, l, u)
