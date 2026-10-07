'''
Study: does the order of the propagation steps matter, and what does a flexible composition buy?

Run:  python studies/propagation_orders.py [samples_per_quest]

1. captures real Questions (every one that reaches propagate.run) from short solver runs;
2. propagates each under all 24 orderings of the four steps (and a few schedules with repeats);
3. compares the final states, the SETS OF COMPLETIONS (all rows solve_question yields from the
   Question), the number of step invocations and the time.
'''
import itertools
import sys
import time
from collections import Counter

import numpy as np

from srg import propagate, solver
from srg.model import NoSolution, PartialSRG, Question

NAMES = tuple(propagate.STEPS)


def capture(quest, n):
    '''the first n distinct-ish Questions that reach propagate.run during a search of `quest`'''
    seen = []
    orig = propagate.run

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


def state(Q):
    '''what is left after propagation, as something comparable'''
    ans = Q.answer
    rows = sorted(zip(map(tuple, Q.A.tolist()), Q.b.tolist()))
    return (tuple(rows), tuple(Q.bounds.tolist()), int(Q.quota), tuple(ans._v.tolist()), tuple(ans._loc.tolist()))


def propagate_with(Q, runner, order):
    Q = Q.copy()
    stats = {}
    t = time.perf_counter()
    try:
        if runner is propagate.run_worklist:
            runner(Q, order, stats)
        else:
            runner(Q, order)
        outcome = state(Q)
    except NoSolution:
        outcome = 'NoSolution'
    return outcome, time.perf_counter() - t, stats


def completions(Q, order):
    '''every candidate row solve_question yields from Q when the steps are used in `order`'''
    old = propagate.ORDER
    propagate.ORDER = order
    try:
        return frozenset(tuple(r) for r in solver.solve_question(Q.copy()))
    finally:
        propagate.ORDER = old


def e2e():
    '''end-to-end solver CPU time for every ordering (exhaustive searches of two small quests)'''
    quests = [(17, 8, 3, 4), (21, 10, 5, 4)]
    configs = []
    for o in itertools.permutations(NAMES):
        configs.append(o)
        configs.append(tuple(n + '*' if n == 'only_1_element_in_row' else n for n in o))
    results = {c: 0.0 for c in configs}
    for rep in range(2):
        for c in configs:
            propagate.ORDER = c
            t = time.process_time()
            for q in quests:
                list(solver.solve(PartialSRG(solver._seed(*q)), max_solutions=None))
            dt = time.process_time() - t
            results[c] = dt if rep == 0 else min(results[c], dt)
    propagate.ORDER = tuple(propagate.STEPS)
    ranked = sorted(results.items(), key=lambda kv: kv[1])
    base = results[('reduce_col', 'eliminate', 'zero_in_b', 'only_1_element_in_row')]
    print(f'end-to-end CPU, {len(quests)} exhaustive searches, best of 2; current default = {base:.2f}s')
    for c, v in ranked[:6]:
        print(f'  {v:6.2f}s  ({base / v:.2f}x)  {" > ".join(c)}')
    print('  ...')
    for c, v in ranked[-3:]:
        print(f'  {v:6.2f}s  ({base / v:.2f}x)  {" > ".join(c)}')


def main():
    if '--e2e' in sys.argv:
        return e2e()
    n = int([a for a in sys.argv[1:] if not a.startswith('--')][0]) if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 60
    quests = [(17, 8, 3, 4), (21, 10, 5, 4), (16, 6, 2, 2), (25, 8, 3, 2)]
    Qs = []
    for q in quests:
        Qs += capture(q, n)
    print(f'{len(Qs)} real Questions captured from {len(quests)} searches\n')

    orders = list(itertools.permutations(NAMES))
    # --- 1. does the order change the fixpoint? -------------------------------------------------
    differ_state = differ_completions = no_solution_disagree = 0
    for Q in Qs:
        outs = [propagate_with(Q, propagate.run, o)[0] for o in orders]
        if len(set(map(repr, outs))) > 1:
            differ_state += 1
            if ('NoSolution' in outs) and not all(o == 'NoSolution' for o in outs):
                no_solution_disagree += 1
        comps = {completions(Q, o) for o in orders[:: 5]}  # 5 of the 24 orders: full search each
        if len(comps) > 1:
            differ_completions += 1
    print('1. order vs result (24 orderings of the 4 steps, each run to a fixpoint)')
    print(f'   Questions whose final propagated state depends on the order : {differ_state} of {len(Qs)}')
    print(f'      ...of which some orders raise NoSolution and others do not : {no_solution_disagree}')
    print(f'   Questions whose SET OF COMPLETIONS depends on the order     : {differ_completions} of {len(Qs)}  (must be 0)\n')

    # --- 2. cost of each ordering ---------------------------------------------------------------
    print('2. cost per ordering (summed over all Questions)')
    rows = []
    for o in orders:
        t = 0.0
        calls = Counter()
        for Q in Qs:
            _, dt, _ = propagate_with(Q, propagate.run, o)
            t += dt
        rows.append((t, o))
    rows.sort()
    for t, o in rows[:3] + rows[-2:]:
        print(f'   {t * 1e3:8.1f} ms  {" > ".join(o)}')
    print(f'   default order: {[t for t, o in rows if o == propagate.ORDER][0] * 1e3:.1f} ms')

    # --- 3. worklist vs repeated rounds ---------------------------------------------------------
    print('\n3. repeated rounds (run) vs worklist (run_worklist), default order')
    t_run = t_wl = 0.0
    calls_run = Counter()
    calls_wl = Counter()
    mismatch = 0
    for Q in Qs:
        o1, d1, _ = propagate_with(Q, propagate.run, None)
        o2, d2, st = propagate_with(Q, propagate.run_worklist, None)
        t_run += d1
        t_wl += d2
        calls_wl.update(st)
        mismatch += (repr(o1) != repr(o2))
    print(f'   final state differs between the two : {mismatch} of {len(Qs)}')
    print(f'   time  run: {t_run * 1e3:.1f} ms   worklist: {t_wl * 1e3:.1f} ms')
    print(f'   worklist step invocations: {dict(calls_wl)} (total {sum(calls_wl.values())})')
    # invocations of the repeated-rounds policy: count by instrumenting the steps
    counts = Counter()
    wrapped = {}
    for name, f in propagate.STEPS.items():
        def make(name, f):
            def g(Q):
                counts[name] += 1
                return f(Q)
            return g
        wrapped[name] = make(name, f)
    saved = dict(propagate.STEPS)
    propagate.STEPS.update(wrapped)
    try:
        for Q in Qs:
            try:
                propagate.run(Q.copy())
            except NoSolution:
                pass
    finally:
        propagate.STEPS.update(saved)
    print(f'   rounds policy step invocations:  {dict(counts)} (total {sum(counts.values())})')


if __name__ == '__main__':
    main()
