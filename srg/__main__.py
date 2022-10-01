#!python
#cython: language_level=3

from .srg import SRG, array
from . import pprint
from . import utils
from . import solver
from . import sorter
import sys


if __name__ == '__main__':
    pprint.clear()

    v, k, l, u = map(int, sys.argv[1:])
    print(v, k, l, u)

    utils.assert_srg(v, k, l, u)

    s = SRG(solver._seed(v, k, l, u))
    ansgen = solver.solve(s)
    ans :list = sorter.sort(ansgen)
    pprint.green('*********** answers *************')
    for ans in ans:
        pprint.green(ans)
