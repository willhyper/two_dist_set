from srg import model
from srg.model import Question, Answer, PartialSRG, array
from srg import solver
from srg import database as db
from srg import sorter
import numpy as np
import pytest

problems_all = []

problems = db.list_problems()
for p in problems:
    v,k,l,u = db.extract_vklu(p)
    if v < 20:
        As = db.get_solutions(v,k,l,u)
        problems_all.append((v,k,l,u, As))


@pytest.mark.parametrize('v,k,l,u, As', problems_all)
def test_solve(v: int, k: int, l: int, u: int, As):
    srg = PartialSRG(solver._seed(v,k,l,u))
    actuals = solver.solve(srg)
    actuals_sorted = sorter.sort(actuals)

    for actual, expected in zip(actuals_sorted, As):
        assert np.array_equal(actual, expected)


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
    assert len(expected) == 2, 'test assumes a quest with more than 1 known solution'

    srg = PartialSRG(solver._seed(v, k, l, u))
    capped = list(solver.solve(srg, max_solutions=1))
    assert len(capped) == 1

    srg = PartialSRG(solver._seed(v, k, l, u))
    uncapped = list(solver.solve(srg, max_solutions=None))
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

