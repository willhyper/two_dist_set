#!python
#cython: language_level=3
import numpy as np
from collections import defaultdict


def lower_upper_bound(A: np.array, b: np.array, bounds: np.array) -> None:
    # A/b/bounds rows are tiny (a handful to ~20 entries), so numpy's
    # per-call dispatch overhead (one nonzero() + N indexed writes per row)
    # costs more than doing this pass in plain Python and writing bounds
    # back once at the end.
    bnd = bounds.tolist()
    for row, lub in zip(A.tolist(), b.tolist()):
        for loc, val in enumerate(row):
            if val and lub < bnd[loc]:
                bnd[loc] = lub
    bounds[:] = bnd


def zero_bound_loc(bounds: np.array) -> np.array:
    return np.where(bounds == 0)[0]


def one_element_row_locs(A: np.array) -> set:
    '''
    example input:

    [0 0 0 0 1] 1 [4]
    [0 0 1 1 0] 1 [2 3]
    [1 0 1 0 0] 0 [0 2]
    [1 1 0 0 0] 1 [0 1]

    defaultdict(<class 'list'>, {0: [4], 1: [2, 3], 2: [0, 2], 3: [0, 1]})

    return {(0,4)}

    '''
    # rows with exactly one non-zero entry, and where it is; if several such rows share a column, the last wins
    rows = np.flatnonzero(A.sum(axis=1) == 1)
    if rows.size == 0:
        return set()
    cols = A[rows].argmax(axis=1)
    crs = dict(zip(cols.tolist(), rows.tolist()))
    return {(r, c) for c, r in crs.items()}
