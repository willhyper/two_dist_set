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

from .model import SRGProperties

# eigenvalues of integer matrices are algebraic numbers; allow float round-off
_EPS = 1e-9


def eigen_rs(v: int, k: int, l: int, u: int) -> tuple:
    '''(r, s): the two non-principal eigenvalues, r > s'''
    d = l - u
    sD = np.sqrt(d * d + 4 * (k - u))
    return (d + sD) / 2, (d - sD) / 2


class Spectrum:
    '''the full spectrum (k, r^f, s^g) of an SRG(v,k,l,u) and of its complement'''

    def __init__(self, v: int, k: int, l: int, u: int):
        r, s = eigen_rs(v, k, l, u)
        _, f, g = SRGProperties(v, k, l, u).multiplicities
        f, g = int(round(f)), int(round(g))
        assert 1 + f + g == v
        self.v = v
        self.r, self.s = r, s
        # descending
        self.spec = np.array([k] + [r] * f + [s] * g)
        self.spec_c = np.array([v - k - 1] + [-1 - s] * g + [-1 - r] * f)


def _interlaces(ev_asc: np.ndarray, spec: np.ndarray) -> bool:
    '''
    Cauchy interlacing of every row of ev_asc (eigenvalues, ascending, of m x m
    principal submatrices) against the eigenvalues spec (descending, length v):
    lambda_i(B) <= lambda_i(A) and lambda_i(B) >= lambda_{i+v-m}(A).
    '''
    m = ev_asc.shape[1]
    v = spec.shape[0]
    ev = ev_asc[:, ::-1]  # descending
    if np.any(ev > spec[:m] + _EPS):
        return False
    if np.any(ev < spec[v - m:] - _EPS):
        return False
    return True


def feasible(M: np.ndarray, spectrum: Spectrum) -> bool:
    '''
    M: partial adjacency matrix, R rows x v columns, first R columns symmetric.

    checks interlacing, against the exact spectrum of the SRG and of its
    complement, on the R x R known block extended by every distinct column of
    the unknown part (each such column is the neighbourhood, within the known
    vertices, of some not-yet-built vertex, so block + column is a principal
    submatrix of the final matrix).
    '''
    R, v = M.shape
    if R == v:
        return True

    block = M[:, :R].astype(np.float64)
    cols = np.unique(M[:, R:], axis=1).T.astype(np.float64)  # (n_distinct, R)
    n = cols.shape[0]

    aug = np.zeros((n, R + 1, R + 1))
    aug[:, :R, :R] = block
    aug[:, :R, R] = cols
    aug[:, R, :R] = cols
    aug[:, R, R] = 0

    if not _interlaces(np.linalg.eigvalsh(aug), spectrum.spec):
        return False

    # complement: J - I - B is a principal submatrix of the complement graph
    comp = 1.0 - aug
    idx = np.arange(R + 1)
    comp[:, idx, idx] = 0
    return _interlaces(np.linalg.eigvalsh(comp), spectrum.spec_c)
