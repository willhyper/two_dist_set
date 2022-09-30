from srg import srg
from srg.srg import Question, Answer, SRG, array
from srg import solver
from srg import database as db
from srg.sort import _sort, sort
import numpy as np
import pytest

problems_all = []

problems = db.list_problems()
for p in problems:
    v,k,l,u = db.extract_vklu(p)
    if v < 20:
        solutions = db.get_solutions(v,k,l,u)
        problems_all.append((v,k,l,u, solutions))


@pytest.mark.parametrize('v,k,l,u, database', problems_all)
def test_solve(v: int, k: int, l: int, u: int, database):
    srg = SRG(solver._seed(v,k,l,u))
    actuals = solver.solve(srg)
    actuals_sorted = list(map(sort, actuals))

    for actual, expected in zip(actuals_sorted, database):
        assert np.array_equal(actual, expected)


@pytest.mark.parametrize('v,k,l,u, database', problems_all)
def test_solve_question(v: int, k: int, l: int, u: int, database):
    expected_rows = [exp[2, 3:] for exp in database]
    
    s = solver._seed(v, k, l, u)
    q = Question.from_matrix(s)    
    actuals = list(solver.solve_question(q)) # actuals are only candidates of real solutions.
    
    for actual in actuals:
        match = map(lambda exp : np.array_equal(exp, actual), expected_rows)
        if any(match):return
    
    assert False, f'actuals {actuals} does not match any in expected {expected_rows}'
    
def test2():
    A = srg.array([[0, 1],
                    [0, 1],
                    [0, 0],
                    [1, 0],
                    [1, 0],
                    [0, 0]])
    b = srg.array([4, 4, 0, 4, 4, 0])

    bound = srg.array([4, 4])
    ans = Answer(value=srg.array([0, -1, 0, 0, -1]), location=srg.array([0, 4, 8, 12, 16]), len=20)
    Q = Question(A, b, 8, bound, ans)

    solver.only_1_element_in_row(Q)
    Q._invariant_check()

