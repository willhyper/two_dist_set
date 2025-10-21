#!python
#cython: language_level=3

from .srg import PartialSRG, SRGProperties, array
from . import pprint
from . import solver
from . import sorter
import sys


if __name__ == '__main__':
    pprint.clear()

    v, k, l, u = map(int, sys.argv[1:])
    print(v, k, l, u)

    assert SRGProperties(v, k, l, u).is_srg(), f'parameters {(v,k,l,u)=} do not form an SRG'

    s = PartialSRG(solver._seed(v, k, l, u))
    ansgen = solver.solve(s)
    ans :list = sorter.sort(ansgen)
    pprint.green('*********** answers *************')
    for ans in ans:
        pprint.green(ans)
