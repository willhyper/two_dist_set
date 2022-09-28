from srg import srg
from srg.srg import Question, Answer
from srg import solver
import numpy as np

def test1():
    
    v, k, l, u = 10, 6, 3, 4

    s = solver._seed(v, k, l, u)

    Q = Question.from_matrix(s, v, k, l, u)

    def ans():
        yield srg.array([1,0,1,0,1,0,1])
        yield srg.array([0,0,1,1,1,1,0])

    for ans_actual, ans_expected in zip(solver.solve(Q), ans()):

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

