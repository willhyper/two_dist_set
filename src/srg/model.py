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

        # quota depends only on _loc/_len, which never change after construction
        # (only _v is mutated in place elsewhere), so compute it once here.
        loc_end_inclusive = np.hstack((self._loc, self._len))  # [0,2,4,6,7]
        self._quota = np.diff(loc_end_inclusive)  # [2,2,2,1]
        assert self._quota.sum() == self._len, f'{self._len} != sum({self._quota})'

    @classmethod
    def default(cls, length: int):
        return Answer(value=ones(length) * cls.UNKNOWN, location=np.arange(length), len=length)

    @property
    def quota(self) -> np.array:
        return self._quota

    @property
    def unknown_loc(self) -> np.array:
        return np.where(self._v == self.UNKNOWN)[0]

    @property
    def unknown(self) -> bool:
        return any(self._v == self.UNKNOWN)

    def copy(self):
        return Answer(self._v.copy(), self._loc.copy(), self._len, self._quota)

    def __eq__(self, other):
        if not np.array_equal(self._v, other._v): return False
        if not np.array_equal(self._loc, other._loc): return False
        if self._len != other._len: return False
        return True

    def __repr__(self):
        return f'Answer(value={repr(self._v)}, \n    location={repr(self._loc)}, len={self._len})'

    def __len__(self):
        return self._len

    def binarize(self)-> array:
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
        assert np.all(_v != self.UNKNOWN), f'answer remains unknown: {_v}'

        _quota = self.quota
        assert np.all(_v <= _quota), f'answer out of quota: {_v} > {_quota}'

        _ans = zeros(self._len)

        ptr = 0
        for c, b in zip(_v, _quota):
            _ans[ptr: ptr + c] = 1
            ptr += b

        return _ans

class Question:
    '''
    given A, b, find x st A @ x = b
    '''

    def __init__(self, A: np.array, b: np.array, quota: int, bounds: np.array, ans: Answer = None):
        R, C = A.shape
        assert R == b.shape[0], f'{R}!=len({b})'
        assert C == bounds.shape[0], f'{C}!=len({bounds})'

        self.A, self.b, self.quota, self.bounds = A, b, quota, bounds

        self._ans = Answer.default(C) if ans is None else ans

    def __str__(self):
        return repr(self)

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
            x=	[? ?]_(2x1)
            bnd	[4 4]	quota=sum(x)=8
            Answer(value=array([ 0, -1,  0,  0, -1], dtype=int8),
                location=array([ 0,  4,  8, 12, 16]), len=20)
        '''


        R, C = self.A.shape
        x = ' '.join('?' * C)
        szx = '(%dx1)' % C

        out = f'b\tA_({R}x{C})\n'
        for b, a in zip(self.b, self.A):
            out += f'{b}\t{a}\n'

        out += f'x=\t[{x}]_{szx}\tquota=sum(x)={self.quota}\n'
        out += f'bnd\t{self._bounds}\n'

        return f'{out}' \
               f'{self._ans}'

    @classmethod
    def from_matrix(cls, m: array):
        v,k,l,u = SRGProperties.from_matrix(m).vklu
        R, C = m.shape
        assert C == v
        known = np.r_[m[:, R], 0]

        # condition l, u
        quota_used = m[:, :R + 1] @ known
        quota = array([l if e else u for e in known[:-1]])

        b = quota - quota_used
        A = m[:, R + 1:]

        # condition k
        # quota_used_k = known.sum()
        # quota_k = k
        unknown_len = v - R - 1
        b_k = k - known.sum()
        a_k = ones(unknown_len)

        A = np.append(A, a_k.reshape(1, unknown_len), axis=0)
        b = np.append(b, b_k)

        if np.any(b < 0):
            raise NoSolution(f'some element in b is negative: b={b}')

        return Question(A, b, quota=b_k, bounds=a_k)

    @property
    def answer(self):
        return self._ans

    @answer.setter
    def answer(self, update: Answer)->None:
        # the number of -1 is same as C = self.A.shape[1]
        num_unknown = len(update.unknown_loc)
        assert num_unknown == self.A.shape[1]

        self._ans = update

    @property
    def bounds(self):
        return self._bounds

    @bounds.setter
    def bounds(self, new_bounds:array)->None:
        assert all(new_bounds >= 0), f'some element in bounds are negative : {new_bounds}'
        self._bounds = new_bounds

    def copy(self):
        return Question(self.A.copy(), self.b.copy(), self.quota, self.bounds.copy(), self.answer.copy())

    def __eq__(self, other):
        if not np.array_equal(self.A, other.A): return False
        if not np.array_equal(self.b, other.b): return False
        if self.quota != other.quota: return False
        if not np.array_equal(self.bounds, other.bounds): return False
        if self.answer != other.answer: return False

        return True

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, new_b):
        assert np.all(new_b>=0), f'some element in b is negative: {new_b}'
        self._b = new_b

    @property
    def quota(self):
        return self._quota

    @quota.setter
    def quota(self, new_quota):
        assert new_quota >= 0, f'new quota should not be negative: {new_quota}'
        self._quota = new_quota

    @property
    def bounds(self):
        return self._bounds

    @bounds.setter
    def bounds(self, new_bounds):
        assert np.all(new_bounds>=0), f'some element in bounds is negative: {new_bounds}'
        self._bounds = new_bounds


    def _invariant_check(self):
        assert np.all(self._b >= 0)
        assert np.all(self._bounds >= 0)
        R, C = self.A.shape
        assert R == self._b.size
        assert C == self._bounds.size
        assert self.answer.unknown_loc.size == C
        assert np.all(self.answer._v <= self.answer.quota)

        if C == 0:
            assert np.all(self._b == 0)

class PartialSRG:
    def __init__(self, mat: array):
        self._matrix = mat

    def complement_matrix(self, maximize: bool = False):
        mat = self._matrix
        R, C = mat.shape
        
        _flip = np.vectorize(lambda t: 0 if t else 1)(mat)
        for r in range(R):
            _flip[r, r] = 0  # diagonal elements are 0
        
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
        ev1, ev2, ev3 = self.eigenvalues
        _, f, g = self.multiplicities

        det = (ev1 ** 1) * (ev2 ** f) * (ev3 ** g)
        return int(det)
