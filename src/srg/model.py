#!python
#cython: language_level=3

import numpy as np
from functools import partial
from . import sorter

dtype = np.int8 # ideal bool
array = partial(np.array, dtype=dtype)
ones = partial(np.ones, dtype=dtype)
zeros = partial(np.zeros, dtype=dtype)
identity = partial(np.identity, dtype=dtype)

class NoSolution(Exception): pass

class Answer:
    '''
    The next row being solved, one entry per class of identical columns.

    _loc[i] is the first column of class i (sorted, _loc[0] == 0), _len the row length, quota[i] the size of class i;
    _v[i] is the number of 1's in class i, or UNKNOWN. Only _v is ever changed in place.
    '''
    __slots__ = ('_v', '_loc', '_len', '_quota')
    UNKNOWN = -1

    def __init__(self, value: np.array, location: np.array, len: int, quota: np.array = None):
        self._v = value
        self._loc = location
        self._len = len

        if quota is not None:  # copy(): _loc/_len are identical, so is the quota
            self._quota = quota
            return

        assert np.array_equal(value.shape, location.shape)
        if location.size > 0:
            assert location[0] == 0
            assert all(np.diff(location)), f'location is not sorted: {location}'
            assert location[-1] < len

        self._quota = np.diff(np.append(location, len))  # [0,2,4,6] with len 7 -> [2,2,2,1]
        assert self._quota.sum() == self._len, f'{self._len} != sum({self._quota})'

    @classmethod
    def default(cls, length: int):
        return Answer(value=ones(length) * cls.UNKNOWN, location=np.arange(length), len=length)

    @property
    def quota(self) -> np.array:
        return self._quota

    @property
    def unknown_loc(self) -> np.array:
        return np.flatnonzero(self._v == self.UNKNOWN)

    @property
    def unknown(self) -> bool:
        return bool((self._v == self.UNKNOWN).any())

    def copy(self):
        return Answer(self._v.copy(), self._loc, self._len, self._quota)  # _loc/_quota are never changed in place

    def __repr__(self):
        return f'Answer(value={repr(self._v)}, \n    location={repr(self._loc)}, len={self._len})'

    def __len__(self):
        return self._len

    def binarize(self) -> array:
        '''
        for example,
        _quota = (3, 4, 4, 2)
        _v = (0, 3, 3, 1)

        this means the first bucket (0, 3) has 0 1's, and 3-0=3 0's
        the 2nd bucket (3,4) has 3 1's, and 4-3=1 0's
        the 3rd bucket is sames as the 2nd
        the 4th bucket (1,2) has 1 1's, and 2-1=1 0's.

        so returns [0 0 0 1 1 1 0 1 1 1 0 1 0] = _ans
                    ^     ^       ^       ^
                    1st   2nd     3rd     4th
        '''
        _v = self._v
        assert (_v != self.UNKNOWN).all(), f'answer remains unknown: {_v}'
        assert (_v <= self._quota).all(), f'answer out of quota: {_v} > {self._quota}'

        _ans = zeros(self._len)
        for start, c in zip(self._loc, _v):
            _ans[start: start + c] = 1
        return _ans


class Question:
    '''
    given A, b, find x st A @ x = b, 0 <= x <= bounds, sum(x) = quota.
    Plain attributes; the propagation steps (propagate.py) keep b, bounds, quota >= 0 or raise NoSolution,
    and _invariant_check() verifies that when debugging.
    '''
    # _eliminated / _zeroed: memos of propagate.eliminate / zero_in_b (skip a step when nothing changed since its last run)
    __slots__ = ('A', 'b', 'quota', 'bounds', 'answer', '_eliminated', '_zeroed')

    def __init__(self, A: np.array, b: np.array, quota: int, bounds: np.array, ans: Answer = None):
        assert A.shape[0] == b.shape[0], f'{A.shape[0]}!=len({b})'
        assert A.shape[1] == bounds.shape[0], f'{A.shape[1]}!=len({bounds})'
        self.A, self.b, self.quota, self.bounds = A, b, quota, bounds
        self.answer = Answer.default(A.shape[1]) if ans is None else ans

    def __repr__(self):
        '''
        example:

            b	A_(6x2)
            4	[0 1]
            4	[0 1]
            0	[0 0]
            4	[1 0]
            4	[1 0]
            0	[0 0]
            x=	[? ?]_(2x1)	quota=sum(x)=8
            bnd	[4 4]
            Answer(value=array([ 0, -1,  0,  0, -1], dtype=int8),
                location=array([ 0,  4,  8, 12, 16]), len=20)
        '''
        R, C = self.A.shape
        out = f'b\tA_({R}x{C})\n'
        for b, a in zip(self.b, self.A):
            out += f'{b}\t{a}\n'
        out += f'x=\t[{" ".join("?" * C)}]_({C}x1)\tquota=sum(x)={self.quota}\n'
        out += f'bnd\t{self.bounds}\n'
        return out + repr(self.answer)

    __str__ = __repr__

    @classmethod
    def from_matrix(cls, m: array):
        v, k, l, u = SRGProperties.from_matrix(m).vklu
        R, C = m.shape
        assert C == v
        known = np.r_[m[:, R], 0]

        # condition l, u
        quota_used = m[:, :R + 1] @ known
        quota = array([l if e else u for e in known[:-1]])

        b = quota - quota_used
        A = m[:, R + 1:]

        # condition k
        unknown_len = v - R - 1
        b_k = k - known.sum()
        a_k = ones(unknown_len)

        A = np.append(A, a_k.reshape(1, unknown_len), axis=0)
        b = np.append(b, b_k)

        if (b < 0).any():
            raise NoSolution(f'some element in b is negative: b={b}')

        return Question(A, b, quota=b_k, bounds=a_k)

    def copy(self):
        return Question(self.A.copy(), self.b.copy(), self.quota, self.bounds.copy(), self.answer.copy())

    def _invariant_check(self):
        assert np.all(self.b >= 0)
        assert np.all(self.bounds >= 0)
        assert self.quota >= 0
        R, C = self.A.shape
        assert R == self.b.size
        assert C == self.bounds.size
        assert self.answer.unknown_loc.size == C
        assert np.all(self.answer._v <= self.answer.quota)

        if C == 0:
            assert np.all(self.b == 0)


class PartialSRG:
    '''the first R rows of an adjacency matrix (R x v int8)'''
    __slots__ = ('_matrix',)

    def __init__(self, mat: array):
        self._matrix = mat

    def complement_matrix(self, maximize: bool = False):
        _flip = 1 - self._matrix
        np.fill_diagonal(_flip, 0)  # diagonal elements are 0 (only the first R of them exist)

        if maximize:
            _flip = sorter.maximize(_flip)
        return PartialSRG(_flip)
    
    def append_and_return_new(self, ans_essential: np.array):
        R, C = self._matrix.shape
        ans_row = np.r_[self._matrix[:, R], 0, ans_essential]
        assert len(ans_row) == C
        return PartialSRG(np.vstack([self._matrix, ans_row]))

    def solved(self):
        M = self._matrix
        v, k, l, u = SRGProperties.from_matrix(M).vklu
        
        R, C = M.shape
        if R != v:
            return False
        
        I = identity(v)
        J = ones((v, v))
        const = (k - u) * I + u * J
        
        return np.array_equal(M @ M - (l - u) * M, const)


    def __repr__(self):
        M = self._matrix
        R, C = M.shape
        dec = [int(''.join(map(str, M[ri, ri+1:])), 2) for ri in range(R-1)] + [0]
        
        # M_repr = np.hstack([M, np.array(dec).reshape(R, 1)])

        # Colored output for diagonal elements with ANSI escape codes
        # GREEN = "\033[92m"
        GRAY = "\033[90m"
        DARKGREEN = "\033[32m"
        END = "\033[0m"

        _repr = ""
        for r in range(R):
            row_ansi = []
            for c in range(C):
                v = str(M[r, c])
                
                if c == r:
                    colored_value = f"{DARKGREEN}{v}{END}"
                    row_ansi.append(colored_value)
                elif c < r:
                    colored_value = f"{GRAY}{v}{END}"
                    row_ansi.append(colored_value)
                else:
                    row_ansi.append(v)
                    
            _repr += ", ".join(row_ansi) + f"\t| {dec[r]}\n"
        
        return _repr

class SRGProperties:
    __slots__ = ('vklu',)

    def __init__(self, v: int, k: int, l: int, u: int):
        self.vklu = (v, k, l, u)

    def is_srg(self) -> bool:
        v, k, l, u = self.vklu
        return (v - k - 1) * u == k * (k - l - 1)

    @classmethod
    def from_matrix(cls, mat: array):
        R, C = mat.shape
        v, k = C, mat[0].sum()
        if mat[0,1] == 1:
            l = mat[0].dot(mat[1])
            u = k * (k - l - 1) // (v - k - 1)    
        else:
            u = mat[0].dot(mat[1])
            l = -u * (v - k - 1) // k  + k - 1
        return SRGProperties(v, k, l, u)
    
    @property
    def conference(self)-> int:
        v, k, l, u = self.vklu
        return 2 * k + (v - 1) * (l - u)

    def complement(self):
        v, k, l, u = self.vklu
        return SRGProperties(v, v - k -1, v -2-2*k +u ,v -2*k +l)
    
    @property
    def eigenvalues(self):
        '''
        return eigenvalues ev1, ev2, ev3
        # https://en.wikipedia.org/wiki/Strongly_regular_graph
        '''
        v, k, l, u = self.vklu
        
        l_minus_u : int = l - u
        sD = np.sqrt(l_minus_u ** 2 + 4 * (k - u))

        ev2 = (l_minus_u + sD) / 2
        ev3 = (l_minus_u - sD) / 2
        ev1 = k

        return ev1, ev2, ev3

    @property
    def multiplicities(self):
        '''
        return multiplicities of eigenvalues ev1, ev2, ev3
        # https://en.wikipedia.org/wiki/Strongly_regular_graph
        '''
        v, k, l, u = self.vklu
        
        conf = self.conference

        if conf == 0: # conference graph
            f = g = (v - 1) // 2
        else:
            v_minus_1 : int = v - 1
            l_minus_u : int = l - u
            sD = np.sqrt(l_minus_u ** 2 + 4 * (k - u))
            
            ConfsD : int = conf // sD
            
            f : int = (v_minus_1 - ConfsD) // 2
            g : int = (v_minus_1 + ConfsD) // 2

        return 1, f, g
    
    @property
    def determinant(self) -> int:
        '''
        exact determinant of the adjacency matrix, det = k * r^f * s^g, in integer arithmetic
        (floating-point eigenvalues lose digits already around v = 29).
        '''
        v, k, l, u = (int(x) for x in self.vklu)
        _, f, g = self.multiplicities
        f, g = int(round(f)), int(round(g))
        if f == g:
            # r and s are the roots of x^2 - (l-u)x - (k-u), so r*s = -(k-u) exactly
            return k * (-(k - u)) ** f
        # f != g: r and s are integers
        _, r, s = self.eigenvalues
        return k * int(round(r)) ** f * int(round(s)) ** g
