import numpy as np
from functools import partial

array = partial(np.array, dtype=np.int8)
ones = partial(np.ones, dtype=np.int8)
zeros = partial(np.zeros, dtype=np.int8)
eye = partial(np.eye, dtype=np.int8)

class NoSolution(Exception): pass

class Answer:
    UNKNOWN = -1

    def __init__(self, value: np.array, location: np.array, len: int):
        #
        assert np.array_equal(value.shape, location.shape)
        if location.size > 0:
            assert location[0] == 0
            assert all(np.diff(location)), f'location is not sorted: {location}'
            assert location[-1] < len

        self._v = value
        self._loc = location
        self._len = len

    @classmethod
    def default(cls, length: int):
        return Answer(value=ones(length) * cls.UNKNOWN, location=np.arange(length), len=length)

    @property
    def quota(self) -> np.array:
        loc_end_inclusive = np.hstack((self._loc, self._len))  # [0,2,4,6,7]
        _quota = np.diff(loc_end_inclusive)  # [2,2,2,1]
        assert _quota.sum() == self._len, f'{self._len} != sum({_quota})'
        return _quota

    @property
    def unknown_loc(self) -> np.array:
        return np.where(self._v == self.UNKNOWN)[0]

    @property
    def unknown(self) -> bool:
        return any(self._v == self.UNKNOWN)

    def copy(self):
        return Answer(self._v.copy(), self._loc.copy(), self._len)

    def __eq__(self, other):
        if not np.array_equal(self._v, other._v): return False
        if not np.array_equal(self._loc, other._loc): return False
        if self._len != other._len: return False
        return True

    def __repr__(self):
        return f'Answer(value={repr(self._v)}, \n    location={repr(self._loc)}, len={self._len})'

    def __len__(self):
        return self._len

    def binarize(self):
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

    def __init__(self, A: np.array, b: np.array, quota: np.int, bounds: np.array, ans: Answer = None):
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
    def from_matrix(cls, m: np.array, v: int, k: int, l: int, u: int):
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

class SRG:
    def __init__(self, mat: array):
        self._matrix = mat

    @property
    def current_matrix(self):
        return self._matrix

    def append_and_return_new(self, ans_essential: np.array):
        _np_array = self._append_and_return_new(ans_essential)
        return SRG(_np_array)

    def _append_and_return_new(self, ans_essential: np.array):
        R, C = self._matrix.shape
        ans_row = np.r_[self._matrix[:, R], 0, ans_essential]
        return np.vstack([self._matrix, ans_row])

    def solved(self):
        R, C = self._matrix.shape
        return R == C

    def __repr__(self):
        return repr(self._matrix)




if __name__ == '__main__':
    v, k, l, u = 10, 6, 3, 4
    from .solver import _seed

    s = _seed(v, k, l, u)
    print('matrix form')
    print(s)

    q = Question.from_matrix(s, v, k, l, u)
    print('transform into problem space')
    print(q)
