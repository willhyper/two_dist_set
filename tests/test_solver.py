from srg import model
from srg.model import Question, Answer, PartialSRG, array
from srg import solver
from srg import database as db
from srg import sorter, canon
import numpy as np
import pytest

problems_all = []

problems = db.list_problems()
for p in problems:
    v,k,l,u = db.extract_vklu(p)
    if v < 20:
        As = db.get_solutions(v,k,l,u)
        problems_all.append((v,k,l,u, As))


def _classes(matrices) -> set:
    '''isomorphism classes of full SRG matrices, via exact canonical form'''
    return {canon.canonical_key(m, leaf_budget=10 ** 7) for m in matrices}


@pytest.mark.parametrize('v,k,l,u, As', problems_all)
def test_solve(v: int, k: int, l: int, u: int, As):
    '''
    solve() yields one representative per isomorphism class, not every vertex
    labeling the database happens to list, so compare isomorphism classes.
    '''
    srg = PartialSRG(solver._seed(v,k,l,u))
    actuals = list(solver.solve(srg))

    assert all(PartialSRG(a).solved() for a in actuals)
    assert _classes(actuals) == _classes(As)


@pytest.mark.parametrize('v,k,l,u, As', problems_all)
def test_solve_without_isomorph_rejection(v: int, k: int, l: int, u: int, As):
    '''
    isomorph_free=False searches every vertex labeling; it must find exactly
    the same isomorphism classes as the pruned search
    '''
    if v > 13: pytest.skip('unpruned search is slow')
    srg = PartialSRG(solver._seed(v,k,l,u))
    actuals = list(solver.solve(srg, isomorph_free=False))
    assert _classes(actuals) == _classes(As)


@pytest.mark.parametrize('v,k,l,u, As', problems_all)
def test_solve_question(v: int, k: int, l: int, u: int, As):
    expected_rows = [exp[2, 3:] for exp in As]
    
    s = solver._seed(v, k, l, u)
    q = Question.from_matrix(s)    
    actuals = list(solver.solve_question(q)) # actuals are only candidates of real solutions.
    
    for actual in actuals:
        match = map(lambda exp : np.array_equal(exp, actual), expected_rows)
        if any(match):return
    
    assert False, f'actuals {actuals} does not match any in expected {expected_rows}'
    
def test_solve_max_solutions_caps_output():
    v, k, l, u = 10, 6, 3, 4
    expected = db.get_solutions(v, k, l, u)
    assert len(expected) == 2, 'test assumes a quest with more than 1 known labeling'

    # isomorph_free=False enumerates every labeling, so there is more than 1
    srg = PartialSRG(solver._seed(v, k, l, u))
    capped = list(solver.solve(srg, max_solutions=1, isomorph_free=False))
    assert len(capped) == 1

    srg = PartialSRG(solver._seed(v, k, l, u))
    uncapped = list(solver.solve(srg, max_solutions=None, isomorph_free=False))
    assert len(uncapped) == len(expected)


def test_solve_default_max_solutions_is_100():
    import inspect
    assert inspect.signature(solver.solve).parameters['max_solutions'].default == 100
    assert solver.DEFAULT_MAX_SOLUTIONS == 100


def test2():
    A = model.array([[0, 1],
                    [0, 1],
                    [0, 0],
                    [1, 0],
                    [1, 0],
                    [0, 0]])
    b = model.array([4, 4, 0, 4, 4, 0])

    bound = model.array([4, 4])
    ans = Answer(value=model.array([0, -1, 0, 0, -1]), location=model.array([0, 4, 8, 12, 16]), len=20)
    Q = Question(A, b, 8, bound, ans)

    solver.only_1_element_in_row(Q)
    Q._invariant_check()



def test_progress_line_counts_are_consistent(monkeypatch):
    '''pending/reached per number of built rows: a finished exhaustive run has nothing pending'''
    monkeypatch.setattr(solver, 'PROGRESS_INTERVAL', 0.0)  # report after every extended partial matrix
    lines = []
    srg = PartialSRG(solver._seed(21, 10, 5, 4))
    list(solver.solve(srg, max_solutions=None, progress=lines.append))

    assert len(lines) > 5
    assert lines[-1].startswith('finished:')
    per_row = dict(item.split(':') for item in lines[-1].split('rows built: ')[1].split())
    assert all(v.split('/')[0] == '0' for v in per_row.values()), per_row  # nothing left pending

    # mid-run lines: pending never exceeds reached, and pending is 0 exactly where the search has finished
    for line in lines[:-1]:
        for item in line.split('rows built: ')[1].split():
            pend, reach = map(int, item.split(':')[1].split('/'))
            assert 0 <= pend <= reach
