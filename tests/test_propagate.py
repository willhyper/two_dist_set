import itertools
import sys

import pytest

from srg import propagate, solver
from srg.model import NoSolution, PartialSRG

NAMES = tuple(propagate.STEPS)


def _capture(quest, n):
    '''the first n Questions that reach propagate.run during a search of `quest`'''
    seen, orig = [], propagate.run

    def spy(Q, order=None):
        if len(seen) < n:
            seen.append(Q.copy())
        return orig(Q, order)

    solver.propagate.run = spy
    try:
        for _ in solver.solve(PartialSRG(solver._seed(*quest)), max_solutions=2):
            if len(seen) >= n:
                break
    finally:
        solver.propagate.run = orig
    return seen


@pytest.fixture(scope='module')
def questions():
    return _capture((17, 8, 3, 4), 30) + _capture((16, 6, 2, 2), 15)


def _completions(Q, order):
    old = propagate.ORDER
    propagate.ORDER = order
    try:
        return frozenset(tuple(r) for r in solver.solve_question(Q.copy()))
    finally:
        propagate.ORDER = old


def test_default_order_uses_every_step_once():
    assert sorted(propagate.ORDER) == sorted(NAMES)


def test_any_order_gives_the_same_completions(questions):
    '''the steps are sound, so the order (and repeats) may change HOW a Question is simplified, never WHAT
    can be completed - including the starred, repeat-until-stable form'''
    orders = list(itertools.permutations(NAMES))[::7] + [
        ('zero_in_b', 'only_1_element_in_row*', 'eliminate', 'reduce_col'),
        ('reduce_col', 'eliminate', 'reduce_col', 'zero_in_b', 'only_1_element_in_row'),  # a step twice in a round
    ]
    for Q in questions:
        results = {_completions(Q, o) for o in orders}
        assert len(results) == 1


def test_orders_can_end_in_different_but_equivalent_states(questions):
    '''the propagation is not confluent: different orders may leave different (equivalent) Questions'''
    def final(Q, order):
        Q = Q.copy()
        try:
            propagate.run(Q, order)
        except NoSolution:
            return 'NoSolution'
        return propagate._fingerprint(Q)

    a, b = NAMES, tuple(reversed(NAMES))
    states = [(final(Q, a), final(Q, b)) for Q in questions]
    # NoSolution is never order-dependent ...
    assert all((x == 'NoSolution') == (y == 'NoSolution') for x, y in states)
    # ... while the leftover state sometimes is (this documents the observation, so a surprise shows up here)
    assert any(x != y for x, y in states)


@pytest.mark.parametrize('name', ['reduce_col', 'eliminate', 'zero_in_b'])
def test_these_steps_are_idempotent(name, questions):
    n = 0
    for Q0 in questions:
        Q = Q0.copy()
        try:
            propagate.STEPS[name](Q)
        except NoSolution:
            continue
        before = propagate._fingerprint(Q)
        propagate.STEPS[name](Q)
        assert propagate._fingerprint(Q) == before, f'{name} changed the Question the second time'
        n += 1
    assert n > 10


def test_only_1_element_in_row_is_not_idempotent(questions):
    '''why it is the step worth repeating: fixing a column can expose a new single-column row'''
    changed = 0
    for Q0 in questions:
        Q = Q0.copy()
        try:
            propagate.STEPS['only_1_element_in_row'](Q)
            before = propagate._fingerprint(Q)
            propagate.STEPS['only_1_element_in_row'](Q)
        except NoSolution:
            continue
        changed += propagate._fingerprint(Q) != before
    assert changed > 0


def test_run_reaches_a_state_no_step_can_change(questions):
    for Q0 in questions:
        Q = Q0.copy()
        try:
            propagate.run(Q)
        except NoSolution:
            continue
        fp = propagate._fingerprint(Q)
        for name in NAMES:
            propagate.STEPS[name](Q)
            assert propagate._fingerprint(Q) == fp, f'{name} still changes the propagated Question'


def test_worklist_reaches_an_equivalent_fixpoint(questions):
    for Q0 in questions:
        a, b = Q0.copy(), Q0.copy()
        raised = []
        for Q, runner in ((a, propagate.run), (b, propagate.run_worklist)):
            try:
                runner(Q)
                raised.append(False)
            except NoSolution:
                raised.append(True)
        assert raised[0] == raised[1]
        if not raised[0]:
            fp = propagate._fingerprint(b)
            for name in NAMES:
                propagate.STEPS[name](b)
                assert propagate._fingerprint(b) == fp, f'{name} still changes the worklist result'
            assert frozenset(tuple(r) for r in solver.solve_question(a)) == frozenset(tuple(r) for r in solver.solve_question(b))
