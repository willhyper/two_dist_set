'''
Completeness check of the whole search pipeline against KNOWN graphs.

For a known SRG G, rebuild it the way the solver does, one row at a time: relabel G to start like solver._seed, then
at every level R look at the first R rows of G (a partial matrix), let solver.advance enumerate every candidate for
row R, and check that G's own row R is among them (up to isomorphism: canonical keys of the extended partial
matrices). The spectral/Gram pruning must accept every prefix too. If any row-enumeration or pruning step ever lost
a real solution, some known graph would fail here at some level.

Run:  python studies/reachability.py [max_v]      (default 45)
'''
import sys
import time

import numpy as np

from srg import canon, database as db, solver, spectral
from srg.model import PartialSRG

BUDGET = 10 ** 6


def seed_order(A, a, b):
    '''vertex order that makes A start like solver._seed: a, b, common neighbours, other neighbours of a, other of b'''
    n = A.shape[0]
    nbr_a = [x for x in range(n) if A[a, x] and x != b]
    common = [x for x in nbr_a if A[b, x]]
    only_a = [x for x in nbr_a if not A[b, x]]
    only_b = [x for x in range(n) if A[b, x] and x != a and not A[a, x]]
    used = {a, b, *common, *only_a, *only_b}
    return [a, b] + common + only_a + only_b + [x for x in range(n) if x not in used]


def reach(A, vklu, budget=BUDGET):
    '''(True, levels) if every row of A is reachable, else (False, level where it failed)'''
    v, k, l, u = vklu
    n = A.shape[0]
    a = 0
    b = int(np.flatnonzero(A[a])[0])
    order = seed_order(A, a, b)
    G = A[np.ix_(order, order)]
    seed = solver._seed(*vklu)
    assert np.array_equal(G[0], seed[0]) and np.array_equal(G[1], seed[1]), 'relabeling must reproduce the seed rows'
    spectrum = spectral.Spectrum(*vklu)

    def arrange(built, unbuilt):
        # identical columns must be contiguous (the solver merges them into classes)
        ub = sorted(unbuilt, key=lambda x: tuple(G[r, x] for r in built))
        return G[np.ix_(built, built + ub)], ub

    built, (M, ub) = [0, 1], arrange([0, 1], list(range(2, n)))
    for R in range(2, n - 1):
        children = solver.advance(PartialSRG(M))
        keys = {canon.canonical_key(c._matrix, budget) for c in children}
        x = ub[0]
        built2 = built + [x]
        M2, ub2 = arrange(built2, ub[1:])
        key2 = canon.canonical_key(M2, budget)
        if key2 not in keys:
            return False, R
        if not spectral.feasible(M2, spectrum):
            return False, -R
        built, M, ub = built2, M2, ub2
    return True, n - 3


def main():
    max_v = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    ok = bad = 0
    for p in sorted(db.list_problems(), key=lambda s: db.extract_vklu(s)):
        q = tuple(db.extract_vklu(p))
        if q[0] > max_v:
            continue
        for i, A in enumerate(db.get_solutions(*q)):
            t = time.time()
            good, where = reach(A, q)
            ok += good
            bad += not good
            print(f'{str(q):18} graph {i}: {"every row reachable" if good else "FAILED at level %d" % where}  '
                  f'({where if good else "-"} levels, {time.time() - t:.1f}s)', flush=True)
    print(f'\n{ok} graphs fully reachable, {bad} failed')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
