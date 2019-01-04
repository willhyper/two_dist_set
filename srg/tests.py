from . import srg
from .srg import Question, Answer



def test2():
    from .solver import _seed
    v, k, l, u = 10, 6, 3, 4

    s = _seed(v, k, l, u)

    Q = Question.from_matrix(s, v, k, l, u)

    def ans():
        yield srg.array([1,0,1,0,1,0,1])
        yield srg.array([0,0,1,1,1,1,0])

    return Q, ans()
