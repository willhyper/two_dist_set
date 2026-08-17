'''
solve for SRG(21, 10, 4, 5), a known-no-solution instance (see
srg/database/problem_21_10_4_5.py), so the search explores the full space without
an early exit on a found answer. Used as the performance benchmark by
profile_performance.sh.
'''
from srg.model import PartialSRG
from srg import solver
from srg.database import problem_21_10_4_5 as p

v, k, l, u = p.v, p.k, p.l, p.u
seed = PartialSRG(solver._seed(v, k, l, u))
solutions = list(solver.solve(seed))
assert solutions == p.solutions, f'expected {p.solutions}, found {solutions}'
print(f'found {len(solutions)} solutions for SRG({v},{k},{l},{u})')
