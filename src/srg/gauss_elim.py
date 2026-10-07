#!python
#cython: language_level=3
'''
Gaussian elimination that keeps the right-hand side non-negative.

The unknown next row of an SRG is a vector x of non-negative integer counts, and every vertex built so
far gives one linear equation about it: a row of the 0/1 matrix A with a right-hand side b >= 0
(A x = b, see model.Question). Textbook Gaussian elimination would simplify A as much as it can, but it
multiplies rows by arbitrary factors and subtracts them freely, which produces fractional entries and
NEGATIVE right-hand sides - and both destroy what this solver needs: A stays a 0/1 matrix (its rows are
stored as bit masks, columns most significant first) and b stays >= 0 (b is a budget: how many more ones
a set of columns may still receive; b < 0 means a contradiction).

So the only row operation used is

    if row m is CONTAINED in row r (every column of m is also in r) and b_r >= b_m:
        replace r by  r - m  (the columns of r that are not in m)  with right-hand side  b_r - b_m

which is exactly the textbook step restricted to the case that is safe here: it only removes ones (A stays
0/1) and b_r - b_m >= 0 (b stays non-negative). The new row is a consequence of the old two, and the pair
(m, r) can be rebuilt from (m, r - m), so the system keeps exactly the same solutions x. The operation is
repeated until it no longer applies: in the result no row contains another. That is the simplest form
reachable by this operation (not a full reduced echelon form: rows like {a,b} and {b,c} stay as they are,
because eliminating b would need a negative coefficient).

x >= 0 also lets the same step expose contradictions, which are raised as model.NoSolution instead of
being left for a later step to notice:
  - m is contained in r but b_r < b_m: then (r - m) . x = b_r - b_m < 0, impossible for x >= 0;
  - a row that is empty (all zero) after subtracting but has b > 0: 0 = b > 0.
(A row that becomes empty with b = 0 is just redundant and is dropped.)

The result has the same number of columns as the input (columns are never removed or reordered here;
dropping columns that were fixed to a value is the job of the callers in solver.py).
'''
import numpy as np
from . import model


def _elim(rows: list) -> None:
    '''
    In-place elimination on rows = [(key, index, b), ...] (key: the 0/1 row as a bit mask), see the module
    docstring.

    Take the row m with the smallest key (the best candidate to be contained in other rows, since a row can
    only contain rows with a numerically smaller or equal key). Every other row that contains m is replaced
    by r - m. If any row was reduced, the keys changed and everything starts over (the rows already set
    aside may now be reducible too); otherwise m is final and is set aside.

    Rows are tiny (a few dozen at most), so plain sorted lists are used. The previous implementation kept
    the rows in heaps and merged them with heapq.merge, a pure-Python generator that was called over a
    million times per minute of search and cost more than the work it organised. The reduction order here
    is exactly the same as before, hence so is the result: this elimination is NOT confluent (different
    orders can end in different, equally valid, systems), so the order is part of the behaviour.
    '''
    pending = [r for r in rows if _nonzero(r)]
    pending.sort()
    done = []  # rows set aside as final, ascending
    while len(pending) > 1:
        m = pending[0]
        mk, mi, mv = m
        reduced, same = [], []
        for r in pending[1:]:
            k, i, v = r
            if mk & k == mk:  # m is contained in r
                if v < mv:
                    raise model.NoSolution(f'row {i} contains row {mi} but has the smaller right-hand side '
                                           f'{v} < {mv}: their difference would equal {v - mv} < 0')
                reduced.append((k - mk, i, v - mv))
            else:
                same.append(r)
        if reduced:
            # an emptied row is redundant if its b is now 0, a contradiction otherwise
            pending = sorted([m] + [r for r in reduced if _nonzero(r)] + same + done)
            done = []
        else:
            done.append(m)
            pending = same
    rows[:] = done + pending  # pending holds at most the last row


def _nonzero(row) -> bool:
    k, i, v = row
    if k:
        return True
    if v != 0:
        raise model.NoSolution(f'row {i} is empty but its right-hand side is {v} != 0')
    return False


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

    # plain Python ints (via tolist()), not numpy scalars: these tuples get
    # pushed through heapq millions of times, and native int comparisons are
    # much cheaper than numpy scalar comparisons.
    weights = 1 << np.arange(C - 1, -1, -1, dtype=np.int64)
    _sum = (A.astype(np.int64) @ weights).tolist()

    return list(zip(_sum, range(R), b.tolist()))
    # including range(R) to keep the tuple comparable in heapq.
    # heapq compares _sum first. if equal items in _sum, heapq compares the next element in the tuple.


def _dec2bin(a):
    '''returns a plain Python list (msb first), not a numpy array: this runs
    once per row per elimination call, so avoiding a numpy array
    construction/reversal here matters. model.zeros(...)[:] = <python list> in
    _decode converts it to numpy in one shot, per row, instead of per bit.'''
    rr = []
    while a:
        rr.append(a & 1)
        a >>= 1
    rr.reverse()
    return rr


def _decode(hd: list, C: int = None) -> tuple:
    '''(A, b) from the encoded rows; C is the number of columns of the original A, which the
    bit masks alone cannot tell (leading columns that are all zero leave no trace in them)'''
    if not hd:
        return model.zeros((0, C or 0)), model.array([])
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

    R = len(_A)
    C = max(map(len, _A)) if C is None else C

    A = model.zeros((R, C))

    for r, _a in enumerate(_A):
        A[r, -len(_a):] = _a

    b = model.array(b)
    return A, b


def sort(A: np.array, b: np.array) -> None:
    argsort = np.argsort(b)
    A[:, :] = A[argsort, :]
    b[:] = b[argsort]


def elim(A: np.array, b: np.array) -> tuple:
    hd = _encode(A, b)
    _elim(hd)
    return _decode(hd, A.shape[1])
