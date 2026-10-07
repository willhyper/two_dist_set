#!python
#cython: language_level=3
'''
Spectral (eigenvalue interlacing) pruning of partial SRG matrices.

An SRG(v,k,l,u) adjacency matrix A has exactly 3 eigenvalues k > r > s, so by
Cauchy interlacing every principal submatrix B of A satisfies

    lambda_min(B) >= s        (A - sI is positive semidefinite)
    lambda_2(B)   <= r        (only the top eigenvalue can exceed r)

These are necessary conditions only: a partial matrix that violates one can
never be completed, so it is safe to discard without losing any solution.
'''
import numpy as np

# eigenvalues of integer matrices are algebraic numbers; allow float round-off
_EPS = 1e-9


def eigen_rs(v: int, k: int, l: int, u: int) -> tuple:
    '''(r, s): the two non-principal eigenvalues, r > s'''
    d = l - u
    sD = np.sqrt(d * d + 4 * (k - u))
    return (d + sD) / 2, (d - sD) / 2


def feasible(M: np.ndarray, r: float, s: float) -> bool:
    '''
    M: partial adjacency matrix, R rows x v columns, first R columns symmetric.

    checks interlacing on the R x R known block, and on that block extended by
    every distinct column of the unknown part (each such column is the
    neighbourhood, within the known vertices, of some not-yet-built vertex, so
    block + column is a principal submatrix of the final matrix).
    '''
    R, v = M.shape
    if R == v:
        return True

    block = M[:, :R].astype(np.float64)
    rest = M[:, R:]
    cols = np.unique(rest, axis=1).T.astype(np.float64)  # (n_distinct, R)
    n = cols.shape[0]

    aug = np.zeros((n, R + 1, R + 1))
    aug[:, :R, :R] = block
    aug[:, :R, R] = cols
    aug[:, R, :R] = cols

    ev = np.linalg.eigvalsh(aug)  # ascending, (n, R+1)
    if ev[:, 0].min() < s - _EPS:
        return False
    if R + 1 >= 2 and ev[:, -2].max() > r + _EPS:
        return False
    return True
