#!python
#cython: language_level=3

from .model import PartialSRG, SRGProperties, array
from . import pprint
from . import solver
from . import sorter
import os
import sys


if __name__ == '__main__':
    pprint.clear()

    args = sys.argv[1:]
    fresh = '--fresh' in args  # ignore any existing checkpoint and start over
    no_checkpoint = '--no-checkpoint' in args
    args = [a for a in args if not a.startswith('--')]
    v, k, l, u = map(int, args[:4])
    max_solutions = int(args[4]) if len(args) > 4 else solver.DEFAULT_MAX_SOLUTIONS
    print(v, k, l, u, f'max_solutions={max_solutions}')

    # progress is saved here, so an interrupted run (Ctrl+C, crash) picks up where it left off
    checkpoint = None if no_checkpoint else f'.srg_checkpoints/srg_{v}_{k}_{l}_{u}_max{max_solutions}.npz'
    if fresh and checkpoint and os.path.exists(checkpoint):
        os.remove(checkpoint)

    assert SRGProperties(v, k, l, u).is_srg(), f'parameters {(v,k,l,u)=} do not form an SRG'

    s = PartialSRG(solver._seed(v, k, l, u))
    def _progress(msg: str):
        print(f'[srg] {msg}', file=sys.stderr, flush=True)

    ansgen = solver.solve(s, max_solutions=max_solutions, progress=_progress, checkpoint=checkpoint)
    ans :list = sorter.sort(ansgen)
    pprint.green('*********** answers *************')
    for ans in ans:
        pprint.green(ans)
