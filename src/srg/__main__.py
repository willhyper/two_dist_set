#!python
#cython: language_level=3

from .model import PartialSRG, SRGProperties, array
from . import pprint
from . import solver
from . import sorter
import sys


if __name__ == '__main__':
    pprint.clear()

    args = sys.argv[1:]
    v, k, l, u = map(int, args[:4])
    max_solutions = int(args[4]) if len(args) > 4 else solver.DEFAULT_MAX_SOLUTIONS
    print(v, k, l, u, f'max_solutions={max_solutions}')

    assert SRGProperties(v, k, l, u).is_srg(), f'parameters {(v,k,l,u)=} do not form an SRG'

    s = PartialSRG(solver._seed(v, k, l, u))
    ansgen = solver.solve(s, max_solutions=max_solutions)
    ans :list = sorter.sort(ansgen)
    pprint.green('*********** answers *************')
    for ans in ans:
        pprint.green(ans)
