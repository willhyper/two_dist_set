import itertools

import numpy as np
import pytest

from srg import gauss_elim
from srg.model import array, NoSolution

# What gauss_elim.elim promises (see the module docstring): the only operation is "subtract a row from a
# row that contains it, when that keeps the right-hand side >= 0", so
#   - A stays a 0/1 matrix and b stays >= 0,
#   - the system keeps exactly the same non-negative solutions x,
#   - in the result no row contains another, and there are no empty rows,
#   - the number of columns is unchanged,
#   - contradictions that the operation exposes are raised as NoSolution.


def test_elim():
    A = array([[1, 1, 1, 1, 1],
               [1, 1, 0, 0, 0],
               [0, 0, 1, 1, 0],
               [1, 1, 1, 1, 0],
               [1, 0, 1, 0, 1]])
    b = array([5, 2, 2, 4, 3])

    Ae, be = gauss_elim.elim(A, b)

    At = array([[0, 0, 0, 0, 1],
                [0, 0, 1, 1, 0],
                [1, 0, 1, 0, 0],
                [1, 1, 0, 0, 0]])
    bt = array([1, 2, 2, 2])

    assert np.array_equal(Ae, At)
    assert np.array_equal(be, bt)


def _solutions(A, b, hi=3):
    '''all x in {0..hi}^C with A x = b (brute force)'''
    C = A.shape[1]
    return {x for x in itertools.product(range(hi + 1), repeat=C) if np.array_equal(A.astype(int) @ np.array(x), b)}


def _random_system(rng, feasible):
    R, C = int(rng.integers(1, 6)), int(rng.integers(1, 5))
    A = rng.integers(0, 2, size=(R, C))
    if rng.random() < 0.5:
        A[-1] = 1  # like the solver, which always has the all-ones row for the total k
    x = rng.integers(0, 4, size=C)
    b = A @ x if feasible else rng.integers(0, 6, size=R)
    return array(A), array(b)


def _no_row_contains_another(A):
    rows = [frozenset(np.flatnonzero(r)) for r in A]
    return not any(i != j and rows[i] <= rows[j] for i in range(len(rows)) for j in range(len(rows)))


@pytest.mark.parametrize('feasible', [True, False])
def test_elim_keeps_the_solutions_and_the_promised_shape(feasible):
    rng = np.random.default_rng(1 if feasible else 2)
    reduced = raised = 0
    for _ in range(600):
        A, b = _random_system(rng, feasible)
        before = _solutions(A, b)
        try:
            Ae, be = gauss_elim.elim(A, b)
        except NoSolution:
            raised += 1
            assert before == set(), 'NoSolution raised for a system that has a solution'
            continue
        # promised invariants
        assert set(np.unique(Ae)) <= {0, 1}, 'A must stay 0/1'
        assert (be >= 0).all(), 'b must stay non-negative'
        assert Ae.shape[1] == A.shape[1], 'column count must not change'
        assert Ae.shape[0] <= A.shape[0] and Ae.shape[0] == be.shape[0]
        assert Ae.sum(axis=1).min(initial=1) >= 1, 'no empty rows'
        assert _no_row_contains_another(Ae), 'a row that contains another should have been reduced'
        # same solutions, exactly
        assert _solutions(Ae, be) == before
        reduced += int(Ae.shape[0] < A.shape[0] or (Ae != A).any())
        if feasible:
            assert before, 'a system built from a solution must have one'
    assert reduced > 50, 'the random systems should exercise the elimination'
    if not feasible:
        assert raised > 50, 'the random infeasible systems should exercise the contradiction detection'


def test_elim_is_idempotent():
    rng = np.random.default_rng(3)
    for _ in range(300):
        A, b = _random_system(rng, True)
        Ae, be = gauss_elim.elim(A, b)
        A2, b2 = gauss_elim.elim(Ae, be)
        assert np.array_equal(Ae, A2) and np.array_equal(be, b2)


@pytest.mark.parametrize('A,b,why', [
    ([[1, 1], [1, 1]], [3, 5], 'x0+x1 cannot be both 3 and 5'),
    ([[1, 0], [1, 1]], [5, 3], 'x0=5 and x0+x1=3 would make x1=-2'),
    ([[0, 0], [1, 1]], [4, 4], 'an empty row cannot equal 4'),
    ([[1, 1, 0], [1, 1, 1]], [4, 3], 'x2 = 3-4 < 0'),
    ([[0, 1, 1], [1, 1, 1], [0, 1, 1]], [2, 1, 2], 'x0 = 1-2 < 0'),
])
def test_elim_raises_on_contradictions(A, b, why):
    with pytest.raises(NoSolution):
        gauss_elim.elim(array(A), array(b))


def test_elim_drops_redundant_rows_without_complaint():
    Ae, be = gauss_elim.elim(array([[1, 1], [1, 1], [0, 0]]), array([3, 3, 0]))
    assert Ae.tolist() == [[1, 1]] and be.tolist() == [3]


def test_elim_keeps_all_zero_columns():
    # the bit masks alone cannot tell that the first column exists
    Ae, be = gauss_elim.elim(array([[0, 1], [0, 1]]), array([2, 2]))
    assert Ae.shape == (1, 2) and Ae.tolist() == [[0, 1]] and be.tolist() == [2]


def test_elim_everything_cancels():
    Ae, be = gauss_elim.elim(array([[0, 0]]), array([0]))
    assert Ae.shape == (0, 2) and be.shape == (0,)


def test_elim_only_ever_subtracts_contained_rows():
    # {a,b}=2 and {b,c}=2 share b but neither contains the other: elimination would need a negative
    # coefficient, so the rows must be left alone (this is not a full echelon form, by design)
    A = array([[1, 1, 0], [0, 1, 1]])
    b = array([2, 2])
    Ae, be = gauss_elim.elim(A, b)
    assert sorted(map(tuple, Ae.tolist())) == sorted(map(tuple, A.tolist()))
    assert sorted(be.tolist()) == [2, 2]
