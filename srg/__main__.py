#!python
#cython: language_level=3

from .srg import SRG, array
from . import pprint
from . import utils
from . import solver
import sys


if __name__ == '__main__':
    pprint.clear()

    v, k, l, u = map(int, sys.argv[1:])
    print(v, k, l, u)

    utils.assert_srg(v, k, l, u)

    s = SRG(solver._seed(v, k, l, u))
    ansgen = solver.solve(s)

    anslist :list = [ans for ans in ansgen]

    pprint.green('*********** answers *************')
    for ans in anslist:
        pprint.green(ans)
