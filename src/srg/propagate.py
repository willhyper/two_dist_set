#!python
#cython: language_level=3
'''
Constraint propagation for the next row of an SRG (see model.Question).

Four cheap deduction steps each simplify a Question without branching:

  reduce_col             merge columns that every equation treats identically
  eliminate              subtract contained rows from each other (gauss_elim.py)
  zero_in_b              columns whose upper bound became 0 are fixed to 0
  only_1_element_in_row  a row with a single remaining column fixes that column

Every step is sound (it never removes a solution) and may raise NoSolution. One step can enable
another, so they are applied until nothing changes. run() does that; the order and the repetitions are
a policy (ORDER), not part of the steps.
'''
from functools import wraps
from itertools import chain
from collections import defaultdict

import numpy as np

from . import gauss_elim, unique, bounds, fork, model
from .model import Question, Answer, NoSolution


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
    answer_new_v = fork.delete(Q.answer._v, col_to_drop_in_ans)
    answer_new_loc = fork.delete(Q.answer._loc, col_to_drop_in_ans)

    Q.A = Q.A[:, col_to_keep]
    Q.bounds = model.array(bounds_new)
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
    _bound_new = fork.delete(Q.bounds, zbls)
    _A_new = fork.delete(Q.A, zbls, axis=1)
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
    Q.A = fork.delete(Q.A, cs, axis=1)
    Q.bounds = fork.delete(Q.bounds, cs)


def _fingerprint(Q: Question) -> tuple:
    '''everything Question.__eq__ compares, as raw bytes: much cheaper than copying Q to compare'''
    ans = Q.answer
    return (Q.A.shape, Q.A.tobytes(), Q.b.tobytes(), Q.bounds.tobytes(), Q.quota,
            ans._v.tobytes(), ans._loc.tobytes())


STEPS = {
    'reduce_col': reduce_col,
    'eliminate': eliminate,
    'zero_in_b': zero_in_b,
    'only_1_element_in_row': only_1_element_in_row,
}

# The order in which the steps are tried in each round. Any order is correct (every step is sound, and the
# set of completions of a Question is the same for all 24 orderings: tested), but not equally fast
# (studies/propagation_orders.py, end-to-end CPU over 48 schedules: 0.96x - 1.14x of the previous default
# reduce_col > eliminate > zero_in_b > only_1_element_in_row). The best schedules all start with the cheap
# step that deletes columns (zero_in_b) and end with the ones that merely tidy up (eliminate, reduce_col).
ORDER = ('zero_in_b', 'only_1_element_in_row', 'eliminate', 'reduce_col')


def _apply(Q: Question, name: str) -> None:
    '''one entry of an order: a step name, or `name*` = repeat that step until it changes nothing'''
    if name.endswith('*'):
        step = STEPS[name[:-1]]
        fp = _fingerprint(Q)
        while True:
            step(Q)
            fp_new = _fingerprint(Q)
            if fp_new == fp:
                return
            fp = fp_new
    else:
        STEPS[name](Q)


def run(Q: Question, order=None) -> None:
    '''
    Apply the steps in `order` (default ORDER), round after round, until a whole round changes nothing. Any
    sequence works, with repeats: ('zero_in_b', 'only_1_element_in_row*', 'eliminate', 'reduce_col'), where
    `name*` repeats that step until it stops changing the Question (only_1_element_in_row is the one step that
    is not idempotent: fixing a column can expose a new single-column row).
    '''
    order = ORDER if order is None else order
    fp = _fingerprint(Q)
    while True:
        for name in order:
            _apply(Q, name)
        fp_new = _fingerprint(Q)
        if fp_new == fp:
            return
        fp = fp_new


# What each step reads. A step needs to run again only if one of these changed since it last ran.
# The deductions are functions of exactly these parts of the Question, which the tests check by comparing
# run_worklist() with run().
READS = {
    'reduce_col': {'A', 'bounds', 'ans'},
    'eliminate': {'A', 'b'},
    'zero_in_b': {'A', 'b', 'bounds', 'ans'},
    'only_1_element_in_row': {'A', 'b', 'bounds', 'ans', 'quota'},
}


# Steps that change nothing when applied a second time in a row (measured on 160 real Questions: 0 changes in
# >= 134 trials each; only_1_element_in_row changed the Question on the second application in 33 of 134).
IDEMPOTENT = {'reduce_col', 'eliminate', 'zero_in_b'}


def _parts(Q: Question) -> dict:
    ans = Q.answer
    return {'A': (Q.A.shape, Q.A.tobytes()), 'b': Q.b.tobytes(), 'bounds': Q.bounds.tobytes(), 'quota': Q.quota,
            'ans': (ans._v.tobytes(), ans._loc.tobytes())}


def run_worklist(Q: Question, order=None, stats: dict = None) -> None:
    '''
    Like run(), but a step is only (re)run when a part of the Question it reads has changed since it last
    ran, instead of blindly repeating whole rounds. The result is a state in which no step can change
    anything, like run(); stats, if given, counts the step invocations.
    '''
    names = tuple(ORDER if order is None else order)
    parts = _parts(Q)
    stale = {name: True for name in names}
    while True:
        for name in names:
            if not stale[name]:
                continue
            STEPS[name](Q)
            if stats is not None:
                stats[name] = stats.get(name, 0) + 1
            new = _parts(Q)
            changed = {k for k in parts if new[k] != parts[k]}
            parts = new
            stale[name] = False
            for other in names:
                if other == name and name in IDEMPOTENT:
                    continue  # running it again right away cannot change anything
                if READS[other] & changed:
                    stale[other] = True
            break  # restart from the first stale step: cheap steps first
        else:
            return

