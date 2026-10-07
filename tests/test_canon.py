import numpy as np
import pytest

from srg import canon, solver, spectral
from srg import database as db
from srg.model import PartialSRG


def _partials():
    '''partial matrices from the first few levels of a small quest'''
    v, k, l, u = 13, 6, 2, 3
    lst = [PartialSRG(solver._seed(v, k, l, u))]
    out = []
    for _ in range(4):
        lst = [n for s in lst for n in solver.advance(s)]
        out += lst
    return out


def test_key_invariant_under_relabeling():
    rng = np.random.default_rng(0)
    for p in _partials()[:60]:
        M = p._matrix
        R, v = M.shape
        perm = np.r_[rng.permutation(R), R + rng.permutation(v - R)]
        assert canon.canonical_key(M[perm[:R]][:, perm]) == canon.canonical_key(M)


def test_key_distinguishes_non_isomorphic():
    ps = _partials()
    keys = {canon.canonical_key(p._matrix) for p in ps}
    # two partial matrices with equal keys must be genuinely relabelings of
    # each other: same row-sum multiset is a cheap necessary check
    by_key = {}
    for p in ps:
        by_key.setdefault(canon.canonical_key(p._matrix), []).append(sorted(p._matrix.sum(axis=1)))
    for sums in by_key.values():
        assert all(s == sums[0] for s in sums)
    assert len(keys) > 1


def test_leaf_budget_falls_back_to_none():
    # a 6-cycle of identical twins is far more symmetric than a budget of 1
    M = np.ones((8, 8), dtype=np.int8) - np.eye(8, dtype=np.int8)
    assert canon.canonical_key(M, leaf_budget=1) is None


def test_spectral_never_rejects_a_database_solution_prefix():
    for p in db.list_problems():
        v, k, l, u = db.extract_vklu(p)
        if v > 21: continue
        spectrum = spectral.Spectrum(v, k, l, u)
        for A in db.get_solutions(v, k, l, u):
            for R in range(2, v + 1):
                assert spectral.feasible(A[:R], spectrum), (v, k, l, u, R)


def test_canonical_matrix_is_a_standard_form():
    rng = np.random.default_rng(1)
    for p in db.list_problems():
        v, k, l, u = db.extract_vklu(p)
        if v > 21: continue
        for A in db.get_solutions(v, k, l, u):
            perm = rng.permutation(v)
            Ac = canon.canonical_matrix(A)
            assert np.array_equal(Ac, canon.canonical_matrix(A[perm][:, perm]))
            assert PartialSRG(Ac).solved()
