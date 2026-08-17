#!python
#cython: language_level=3
import numpy as np
from collections import defaultdict
from . import srg


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
    rows, cols = A.nonzero()
    nz = defaultdict(list)
    for rnz, cnz in zip(rows.tolist(), cols.tolist()):
        nz[rnz].append(cnz)

    # reduce rcs so that columns are unique. Corresponding rows dont matter
    # {(0, 1), (3, 0), (1, 1), (4, 0)} => { 1:1, 0:4 }
    crs = {clist[0]:r for r, clist in nz.items() if len(clist) == 1}

    return {(r, c) for c, r in crs.items()}



if __name__ == '__main__':
    def test1():
        A = srg.array([[0, 0, 0, 0, 1],
                       [0, 0, 1, 1, 0],
                       [1, 0, 1, 0, 0],
                       [1, 1, 0, 0, 0]])
        b = srg.array([1, 1, 0, 1])
        bound = srg.array([1, 1, 1, 1, 1])

        print('original upper bounds', bound)
        lower_upper_bound(A, b, bound)
        print('new lower upper bounds', bound)
        assert np.array_equal(bound, [0, 1, 0, 1, 1])

        rcs = one_element_row_locs(A)
        print('one element rows (r,c)=', rcs)
        assert np.array_equal(rcs.pop(), (0, 4))


    A = srg.array([[0, 1], [0, 1], [0, 0], [1, 0], [1, 0], [0, 0]])
    b = srg.array([4, 4, 0, 4, 4, 0])
    bound = srg.array([4, 4])

    print('original upper bounds', bound)
    lower_upper_bound(A, b, bound)
    print('new lower upper bounds', bound)

    rcs = one_element_row_locs(A)
    print('one element rows (r,c)=', rcs)
