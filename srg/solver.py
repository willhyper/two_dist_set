#!python
#cython: language_level=3

from itertools import chain

import numpy as np
from collections import defaultdict
from . import gauss_elim, unique, bounds, fork, srg
from . import pprint
from .srg import Question, Answer, NoSolution
from .utils import debug
from functools import wraps

def _seed(v: int, k: int, l: int, u: int) -> np.array:
    remain_ones_number = k - l - 1

    s = srg.zeros((2, v))
    s[0, 1:k + 1] = 1  # 1st row
    s[1, 2:l + 2] = 1  # 2nd row under 1's
    s[1, k + 1:k + remain_ones_number + 1] = 1  # 2nd row under 0's.

    s[1, 0] = s[0, 1]

    return s


def raiseExceptionIfNotSolvableAfterwards(func):

    @wraps(func)
    def wrapped(Q: Question):

        result = func(Q) # func itself can also raise NoSolution exception
        ans = Q.answer

        R, C = Q.A.shape
        if C == 0 and any(Q.b != 0):
            raise NoSolution(f'after {func.__name__}, no answer can equate nonzero b: b={Q.b}')

        assert Q.bounds.size == C , "design error"

        if Q.bounds.size > 0 and Q.bounds.sum() < Q.quota:
            raise NoSolution(f'after {func.__name__}, cannot reach quota from bound: sum({Q.bounds})={Q.bounds.sum()} < {Q.quota}')
        if np.any(ans._v > ans.quota):
            raise NoSolution(f'after {func.__name__}, answer out of quota: {ans._v}>{ans.quota}')



        return result

    return wrapped



#@debug
@raiseExceptionIfNotSolvableAfterwards
def reduce_col(Q: Question) -> None:
    R, C = Q.A.shape
    if C < 2: return

    d = defaultdict(list)
    enc = unique._encode(Q.A)  # [7,7,5,5,3,3,1]
    for category, loc in zip(enc, range(C)):
        d[category].append(loc)  # defaultdict(<class 'list'>, {7: [0, 1], 5: [2, 3], 3: [4, 5], 1: [6]})

    col_to_keep, col_to_drop, bounds_new = zip(*((locs[0], locs[1:], Q.bounds[locs].sum()) for category, locs in
                                                 d.items()))  # [(0, 2), (2, 2), (4, 2), (6, 1)]

    col_to_drop_in_A = list(chain(*col_to_drop))
    col_to_drop_in_ans = Q.answer.unknown_loc[col_to_drop_in_A]
    answer_new_v = np.delete(Q.answer._v, col_to_drop_in_ans)
    answer_new_loc = np.delete(Q.answer._loc, col_to_drop_in_ans)

    Q.A = Q.A[:, col_to_keep]
    Q.bounds = srg.array(bounds_new)
    Q.answer = Answer(value=answer_new_v, location=answer_new_loc, len=len(Q.answer))


#@debug
@raiseExceptionIfNotSolvableAfterwards
def eliminate(Q: Question) -> None:
    R, C = Q.A.shape
    if C == 0: return
    Ae, be = gauss_elim.elim(Q.A, Q.b)
    Q.A, Q.b = Ae, be


#@debug
@raiseExceptionIfNotSolvableAfterwards
def zero_in_b(Q: Question) -> None:
    '''
    if element in bounds is 0, respective element in answer is 0
    '''
    #
    bounds.lower_upper_bound(Q.A, Q.b, Q.bounds)
    #
    ans: Answer = Q.answer
    val_unknown_locs = ans.unknown_loc
    assert np.array_equal(val_unknown_locs.shape, Q.bounds.shape)

    zbls = bounds.zero_bound_loc(Q.bounds)
    for zbl in zbls:
        zero_loc = val_unknown_locs[zbl]
        ans._v[zero_loc] = 0  # Q.answer updated in place
    _bound_new = np.delete(Q.bounds, zbls)
    _A_new = np.delete(Q.A, zbls, axis=1)
    Q.A, Q.bounds = _A_new, _bound_new



#@debug
@raiseExceptionIfNotSolvableAfterwards
def only_1_element_in_row(Q: Question):
    '''
    if only 1 element in a row r is non-zero, b[r] is the answer to respective element in answer
    :return proceed as bool
    '''
    #
    ans: Answer = Q.answer
    val_unknown_locs = ans.unknown_loc
    assert np.array_equal(val_unknown_locs.shape, Q.bounds.shape)

    #
    rcs = bounds.one_element_row_locs(Q.A)  # [(0,4), (1,2), (2,0)]
    if not rcs: return
    rs = [r for r, c in rcs]  # [0,1,2]
    cs = [c for r, c in rcs]  # [4,2,0]

    subA = Q.A[:, cs]
    subx = Q.b[rs]
    b_to_update = subA @ subx

    # check eligibility, dont assign/update Question until check
    for r, c in rcs:
        if Q.b[r] > Q.bounds[c]:
            raise NoSolution(f'{Q.b[r]} = Q.b[{r}] > Q.bounds[{c}] = {Q.bounds[c]}')

    if subx.sum() > Q.quota:
        raise NoSolution(f'sum({subx})={subx.sum()} > {Q.quota} = Q.quota')

    if np.any(b_to_update > Q.b):
        raise NoSolution(f'b_to_update={b_to_update} > {Q.b} = Q.b')

    # check done, update Question now
    # update answer, reduce quota
    for r, c in rcs:
        val_b_loc = val_unknown_locs[c]
        ans._v[val_b_loc] = Q.b[r]
        Q.quota -= Q.b[r] # because check above, Q.quota remains non-negative

    # update b, reduce bounds, reduce A
    Q.b -= b_to_update # because check above, Q.b remains non-negative
    Q.A = np.delete(Q.A, cs, axis=1)
    Q.bounds = np.delete(Q.bounds, cs)


#@debug
@raiseExceptionIfNotSolvableAfterwards
def fork_enum(Q: Question):
    '''
    strategy is to pick the minimum bound to enumerate.

    :param Q: A question whose answer remains unknown
    :return:
    '''
    ans_unknown_loc = Q.answer.unknown_loc
    assert len(ans_unknown_loc) > 0

    minloc = np.argmin(Q.bounds)
    new_bound = np.delete(Q.bounds, minloc)
    Aminloc, new_A = fork._pop_col(Q.A, minloc)

    for q_used, q_rest in fork.enum(Q.quota, Q.bounds, minloc):
        #
        new_b = Q.b - Aminloc * q_used
        if np.any(new_b < 0): continue
        #
        new_ans: Answer = Q.answer.copy()
        ans_loc = ans_unknown_loc[minloc]
        new_ans._v[ans_loc] = q_used
        #
        yield Question(new_A.copy(), new_b, quota=q_rest, bounds=new_bound.copy(), ans=new_ans)

    # todo: delete Q?



def solve(Q: Question):
    stack = list()
    stack.append(Q)

    while stack:
        Q : Question = stack.pop()

        try:
            while True:
                Qdummy = Q.copy()
                reduce_col(Q)
                eliminate(Q)
                zero_in_b(Q)
                only_1_element_in_row(Q)
                if Q == Qdummy:
                    break

            if Q.answer.unknown:
                for Qnext in fork_enum(Q):
                    # pprint.red(Qnext)
                    stack.append(Qnext)
            else:
                ans = Q.answer.binarize()
                yield ans

        except NoSolution as e:
            # pprint.red(e)
            # pprint.red(Q)
            continue


if __name__ == '__main__':

    pprint.clear()


    def test1():
        from ..tests import tests

        Q, ansgen = tests.test2()
        for ans_actual, ans_expected in zip(solve(Q), ansgen):
            pprint.green(ans_expected)
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

        only_1_element_in_row(Q)
        Q._invariant_check()


    test1()
    test2()
