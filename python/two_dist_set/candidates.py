__author__ = 'chaoweichen'

import numpy as np
import itertools


def _cumsum(A):
    col = len(A[-1]) # 6
    cumsum = np.zeros(col-1, dtype=np.int)
    for p, a in enumerate(reversed(A), start=1):
        temp = np.array( a[1-col:] )
        cumsum += temp << p
    return cumsum


def generate(A):
    k = sum(A[0]) # 4
    col = len(A[-1]) # 6
    used = sum(a[-col] for a in A) # 2

    if used > k:
        return

    cumsum = _cumsum(A)

    v = len(A[0])+1
    r = len(A)+1

    def is_maintain_reverse_sorted_when_adding_1_at(indices):
        for i in indices:
            if i == 0:
                continue
            #elif cumsum[i] +1 > cumsum[i-1] + (1 if i-1 in indices else 0):
            elif cumsum[i] > (cumsum[i-1] if i-1 in indices else cumsum[i-1]-1):
                return False

        return True

    for indices in itertools.combinations(range(v-r), k-used):
        if is_maintain_reverse_sorted_when_adding_1_at(indices):
            candidate = np.zeros(v-r, dtype=np.int)
            candidate[[indices]] = 1
            yield candidate


def test_io():

    A = ((1, 1, 1, 1, 0, 0, 0, 0),
            (0, 0, 0, 1, 1, 1, 0),
               (1, 1, 1, 0, 0, 0),)

    Amat =[[0, 1, 1, 1, 1, 0, 0, 0, 0],
           [1, 0, 0, 0, 0, 1, 1, 1, 0],
           [1, 0, 0, 1, 1, 1, 0, 0, 0],
           [1, 0, 1, 0, 0, 0, 0, 0, 0]]

    Ans = [ [1, 1, 0, 0, 0],
            [1, 0, 1, 0, 0],
            [1, 0, 0, 0, 1],
            [0, 1, 1, 0, 0],
            [0, 1, 0, 0, 1],
            [0, 0, 1, 1, 0],
            [0, 0, 1, 0, 1],
           ]
    for c, a in zip(generate(A), Ans):
        aa = np.array(a, dtype=np.int)
        assert np.array_equal(c,aa)

def test_cumsum():
    A = ((1, 1, 1, 1, 0, 0, 0, 0),
            (0, 0, 0, 1, 1, 1, 0),
               (1, 1, 1, 0, 0, 0),)

    ans = np.array([10,6,4,4,0], dtype=np.int)
    cs = _cumsum(A)
    assert np.array_equal(cs, ans)

if __name__ == '__main__':
    test_io()
    test_cumsum()
    pass


