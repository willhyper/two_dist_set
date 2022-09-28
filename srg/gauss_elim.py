#!python
#cython: language_level=3
import heapq
import numpy as np
from . import srg


def _remove_zerokeys(h: list) -> None:
    hnz = [(k, i, v) for k, i, v in h if k > 0]
    h.clear()
    h += hnz


def _gauss_elim(hd: list) -> bool:
    '''

    :param hd: a sorted list.
    :param b: non-negative array, putting constrain on hd

    :return: reducible bool. True if reducible. False otherwise.
    '''

    # classifies hd into 3 classes: min, reducible, same
    mk, mi, mv = heapq.heappop(hd)
    assert mk > 0, "zero key found!!! design error"
    reducible, same = [], []  # will maintain sorted order
    while hd:
        k, i, v = heapq.heappop(hd)
        if mk & k == mk and v >= mv:
            reducible.append((k - mk, i, v - mv))
        else:
            same.append((k, i, v))
    # (mk, mi, mv), reducible, same
    # hd is redistributed into these 3 categories

    if reducible:
        _remove_zerokeys(reducible)
        hd += list(heapq.merge([(mk, mi, mv)], reducible, same))
        return True
    else:
        hd += list(heapq.merge([(mk, mi, mv)], same))
        return False


def _elim(hd: list) -> None:
    #
    _remove_zerokeys(hd)

    #
    if len(hd) <= 1: return

    #
    hd.sort()

    #
    hs = []
    while hd:
        simplified = _gauss_elim(hd)
        if simplified:  # start over
            temp = list(heapq.merge(hs, hd))
            hs.clear()
            hd.clear()
            hd += temp
        else:
            _mk_mi_mv = heapq.heappop(hd)
            hs.append(_mk_mi_mv)

    hd += hs


def _encode(A: np.array, b: np.array) -> list:
    '''
    A = np.array([[1, 1, 1, 1, 1],
                  [1, 1, 0, 0, 0],
                  [0, 0, 1, 1, 0],
                  [1, 1, 1, 1, 0],
                  [1, 0, 1, 0, 1]], dtype=np.int8)
    b = np.array( [5, 2, 2, 4, 3], dtype=np.int8)

    :return:
    [(31, 0, 5),
     (24, 1, 2),
     ( 6, 2, 2),
     (30, 3, 4),
     (21, 4, 3)]
    '''
    R, C = A.shape
    assert b.size == R, f'{b.size} != {R}'

    _sum = A[:, -1].copy().astype(int)
    for c in reversed(range(C - 1)):
        delta = A[:, c].astype(int) << (C - 1 - c)
        _sum += delta

    return list(zip(_sum, range(R), b))
    # including range(R) to keep the tuple comparable in heapq.
    # heapq compares _sum first. if equal items in _sum, heapq compares the next element in the tuple.


def _dec2bin(a):
    rr = []
    while a:
        r = a % 2
        a >>= 1  # a //= 2
        rr.append(r)
    return srg.array(rr)[::-1]


def _decode(hd: list) -> tuple:
    z = zip(*hd)
    enc_a, ind, b = next(z), next(z), next(z)

    # enc_a = (31, 24, 6, 30, 21)
    #
    # ind = (0, 1, 2, 3, 4)
    #

    _A = list(map(_dec2bin, enc_a))
    # _A = [array([1, 1, 1, 1, 1], dtype=int8),
    #       array([1, 1, 0, 0, 0], dtype=int8),
    #       array([1, 1, 0], dtype=int8),
    #       array([1, 1, 1, 1, 0], dtype=int8),
    #       array([1, 0, 1, 0, 1], dtype=int8)]

    R, C = len(_A), max(map(len, _A))

    A = srg.zeros((R, C))

    for r, _a in enumerate(_A):
        A[r, -len(_a):] = _a

    b = srg.array(b)
    return A, b


def sort(A: np.array, b: np.array) -> None:
    argsort = np.argsort(b)
    A[:, :] = A[argsort, :]
    b[:] = b[argsort]


def elim(A: np.array, b: np.array) -> tuple:
    hd = _encode(A, b)
    _elim(hd)
    return _decode(hd)


if __name__ == '__main__':
    A = srg.array([[1, 1, 1, 1, 1],
                   [1, 1, 0, 0, 0],
                   [0, 0, 1, 1, 0],
                   [1, 1, 1, 1, 0],
                   [1, 0, 1, 0, 1]])
    b = srg.array([5, 2, 2, 4, 3])

    Ae, be = elim(A, b)

    At = srg.array([[0, 0, 0, 0, 1],
                    [0, 0, 1, 1, 0],
                    [1, 0, 1, 0, 0],
                    [1, 1, 0, 0, 0]])
    bt = srg.array([1, 2, 2, 2])

    assert np.array_equal(Ae, At)
    assert np.array_equal(be, bt)
