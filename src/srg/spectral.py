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
        self.f, self.g = f, g
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


# Gram-completion thresholds. A matrix is only rejected on a *clear* violation,
# and an eigenvalue in the grey zone between ZERO and POSITIVE makes the check
# give up (return True), so float round-off can never discard a real solution.
_ZERO = 1e-8
_POSITIVE = 1e-5
_VIOLATION = 1e-4


def _gram_ok(block: np.ndarray, cols: np.ndarray, s: float, dim: int) -> bool:
    '''
    A - sI is positive semidefinite of rank dim, i.e. the Gram matrix of vectors
    in R^dim (diagonal -s, off-diagonal the 0/1 adjacency). Let P = block - sI
    be the Gram matrix of the built vertices (R x R) and cols (R x m) their
    adjacency to m not-yet-built vertices. If P already has rank dim, the built
    vertices span the whole space, so every not-yet-built vertex is determined by
    its column: it must lie in range(P) with squared norm -s, and the inner
    product of any two of them (their adjacency) must be exactly 0 or 1.
    Returns False only if that is clearly violated.
    '''
    R = block.shape[0]
    w, V = np.linalg.eigh(block - s * np.eye(R))
    if w[0] < -_POSITIVE:
        return False  # not PSD (interlacing rejects this already)
    if np.any((w > _ZERO) & (w < _POSITIVE)):
        return True  # grey zone: cannot tell the rank reliably
    pos = w >= _POSITIVE
    rank = int(pos.sum())
    if rank > dim:
        return False
    if rank < dim or cols.shape[1] == 0:
        return True  # built vertices do not span the space yet: nothing is determined

    Vr, wr = V[:, pos], w[pos]
    coords = Vr.T @ cols  # (rank, m)
    if np.abs(cols - Vr @ coords).max() > _VIOLATION:
        return False  # a not-yet-built vertex lies outside the span
    C = (coords.T / wr) @ coords  # (m, m) inner products of the determined vertices
    if np.abs(np.diag(C) + s).max() > _VIOLATION:
        return False  # wrong squared norm
    off = C - np.diag(np.diag(C))
    dist01 = np.minimum(np.abs(off), np.abs(off - 1.0))
    np.fill_diagonal(dist01, 0.0)
    return dist01.max() <= _VIOLATION  # off-diagonal entries must be 0 or 1


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
    if not _interlaces(np.linalg.eigvalsh(comp), spectrum.spec_c):
        return False

    # Gram completion, for the graph (smallest eigenvalue s, A - sI has rank f+1)
    # and for its complement (smallest eigenvalue -1-r, rank g+1)
    allcols = M[:, R:].astype(np.float64)
    if not _gram_ok(block, allcols, spectrum.s, spectrum.f + 1):
        return False
    block_c = 1.0 - block
    np.fill_diagonal(block_c, 0.0)
    return _gram_ok(block_c, 1.0 - allcols, -1.0 - spectrum.r, spectrum.g + 1)
