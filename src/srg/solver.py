#!python
#cython: language_level=3

import time
from itertools import chain
from typing import Callable, Iterator, Optional
from .model import array
from .model import PartialSRG, SRGProperties
import numpy as np
from collections import defaultdict
from . import gauss_elim, unique, bounds, fork, model, spectral, canon, propagate
from .propagate import raiseExceptionIfNotSolvableAfterwards, reduce_col, eliminate, zero_in_b, only_1_element_in_row  # noqa: F401 (kept importable from here)
from .model import Question, Answer, NoSolution
from .utils import debug
from functools import wraps
from functools import reduce

# Once a quest's existence question is settled, further enumeration has
# diminishing value - a quest with a lot of symmetry can have on the order of
# n! solutions (see e.g. srg/database/problem_25_12_5_6.py's docstring).
# solve() stops advancing the search once it has yielded this many matrices,
# unless the caller passes max_solutions=None for an uncapped (exhaustive) run.
DEFAULT_MAX_SOLUTIONS = 100


def _seed(v: int, k: int, l: int, u: int) -> np.array:
    remain_ones_number = k - l - 1

    s = model.zeros((2, v))
    s[0, 1:k + 1] = 1  # 1st row
    s[1, 2:l + 2] = 1  # 2nd row under 1's
    s[1, k + 1:k + remain_ones_number + 1] = 1  # 2nd row under 0's.

    s[1, 0] = s[0, 1]

    return s


#@debug
@raiseExceptionIfNotSolvableAfterwards
def fork_enum(Q: Question):
    '''
    strategy is to pick the minimum bound to enumerate.

    :param Q: A question whose answer remains unknown
    :return:
    '''
    ans_unknown_loc = Q.answer.unknown_loc
    assert len(ans_unknown_loc) > 0

    minloc = np.argmin(Q.bounds)
    new_bound = fork.delete(Q.bounds, minloc)
    Aminloc, new_A = fork._pop_col(Q.A, minloc)

    for q_used, q_rest in fork.enum(Q.quota, Q.bounds, minloc):
        #
        new_b = Q.b - Aminloc * q_used
        if (new_b < 0).any(): continue
        #
        new_ans: Answer = Q.answer.copy()
        ans_loc = ans_unknown_loc[minloc]
        new_ans._v[ans_loc] = q_used
        #
        yield Question(new_A.copy(), new_b, quota=q_rest, bounds=new_bound.copy(), ans=new_ans)

    # todo: delete Q?



def solve_question(Q: Question)->Iterator[array]:
    stack = list()
    stack.append(Q)

    while stack:
        Q : Question = stack.pop()

        try:
            propagate.run(Q)

            if Q.answer.unknown:
                for Qnext in fork_enum(Q):
                    stack.append(Qnext)
            else:
                ans = Q.answer.binarize()
                yield ans

        except NoSolution:
            continue


def partition_by_done(lst : Iterator[PartialSRG]):
    lst_done, lst_undone = [], []
    [lst_done.append(s) if s.solved() else lst_undone.append(s) for s in lst]
    return lst_done, lst_undone

def advance(s : PartialSRG) -> Iterator[PartialSRG]:
    assert not s.solved()
    try:
        q = Question.from_matrix(s._matrix)
    except NoSolution:
        return []
    ansgen_arr : Iterator[array] = solve_question(q)
    return list(map(s.append_and_return_new, ansgen_arr))

PROGRESS_INTERVAL = 5.0  # seconds between progress lines


def _fresh(seen: set, matrix: np.ndarray, isomorph_free: bool) -> bool:
    '''
    True if this matrix is the first of its isomorphism class to be seen
    (and records it). Matrices too symmetric to canonize always count as fresh.
    '''
    if not isomorph_free:
        return True
    key = canon.canonical_key(matrix)
    if key is None:
        return True
    if key in seen:
        return False
    seen.add(key)
    return True


def solve(srg: PartialSRG, max_solutions: Optional[int] = DEFAULT_MAX_SOLUTIONS,
          progress: Optional[Callable[[str], None]] = None, isomorph_free: bool = True):
    '''
    yields completed adjacency matrices as soon as each is found, searching
    depth-first over partially-built rows (each partial matrix is extended by
    one row at a time, see advance()), and stops once max_solutions have been
    yielded - this only settles existence quickly instead of paying to
    enumerate every symmetry of a solution-rich quest. Pass max_solutions=None
    to disable the cap and enumerate exhaustively.

    Every partial matrix is checked with eigenvalue interlacing (spectral.py)
    and, unless isomorph_free=False, only the first partial matrix of each
    isomorphism class (per number of rows built) is ever extended (canon.py):
    isomorphic partial matrices have the same completions, so this loses
    nothing. The matrices yielded are therefore one representative per
    isomorphism class of solution, not every vertex-labeling of each.

    progress, if given, is called with a one-line status string every
    PROGRESS_INTERVAL seconds: how many partial matrices (isomorphism classes)
    were reached at each number of built rows, and how many are still waiting
    on the stack at each. Exhaustive searches finish when the stack empties.
    '''
    t_start = last = time.time()
    v, k, l, u = SRGProperties.from_matrix(srg._matrix).vklu
    spectrum = spectral.Spectrum(v, k, l, u)

    seen = defaultdict(set)  # rows built -> classes of partial matrices already reached
    seen_done = set()
    reached = defaultdict(int)  # rows built -> number of classes reached (for progress)
    pending = defaultdict(int)  # rows built -> number of those still on the stack (kept incrementally)
    stack = [srg]
    pending[srg._matrix.shape[0]] += 1
    yielded = 0
    explored = 0

    def status() -> str:
        rows = sorted(set(reached) | set(pending))
        per_row = ' '.join(f'{r}:{pending[r]}/{reached[r]}' for r in rows)
        return (f'explored {explored} partial matrices, {yielded} solutions, {time.time() - t_start:.0f}s elapsed; '
                f'pending/reached by rows built: {per_row}')

    while stack and (max_solutions is None or yielded < max_solutions):
        partial = stack.pop()
        pending[partial._matrix.shape[0]] -= 1
        explored += 1

        children = []
        for child in advance(partial):
            if child.solved():
                if _fresh(seen_done, child._matrix, isomorph_free):
                    yielded += 1
                    yield child._matrix
                    if max_solutions is not None and yielded >= max_solutions:
                        break
            elif spectral.feasible(child._matrix, spectrum) \
                    and _fresh(seen[child._matrix.shape[0]], child._matrix, isomorph_free):
                reached[child._matrix.shape[0]] += 1
                children.append(child)
        stack.extend(reversed(children))  # the first child is explored first
        for child in children:
            pending[child._matrix.shape[0]] += 1

        if progress and time.time() - last >= PROGRESS_INTERVAL:
            last = time.time()
            progress(status())

    if progress:
        progress(('finished' if not stack else 'stopped at max_solutions') + ': ' + status())
