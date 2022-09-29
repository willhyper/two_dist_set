from srg import srg
from srg.srg import Question, Answer, SRG
from srg import solver
from srg import database as db
from srg.sort import sort as srg_sort
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
    actuals_sorted = list(map(srg_sort, actuals))

    for actual, expected in zip(actuals_sorted, database):
        np.array_equal(actual, expected)

def test1():
    
    v, k, l, u = 10, 6, 3, 4

    s = solver._seed(v, k, l, u)

    Q = Question.from_matrix(s)

    def ans():
        yield srg.array([1,0,1,0,1,0,1])
        yield srg.array([0,0,1,1,1,1,0])

    for ans_actual, ans_expected in zip(solver.solve_question(Q), ans()):

        assert np.array_equal(ans_actual, ans_expected)





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

