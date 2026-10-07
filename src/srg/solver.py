#!python
#cython: language_level=3

import random
import time
from itertools import chain
from typing import Callable, Iterator, Optional
from .model import array
from .model import PartialSRG, SRGProperties
import numpy as np
from collections import defaultdict
from . import gauss_elim, unique, bounds, fork, model, spectral, canon
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

    s = model.bzeros((2, v))
    s[0, 1:k + 1] = 1  # 1st row
    s[1, 2:l + 2] = 1  # 2nd row under 1's
    s[1, k + 1:k + remain_ones_number + 1] = 1  # 2nd row under 0's.

    s[1, 0] = s[0, 1]

    return s


def raiseExceptionIfNotSolvableAfterwards(func):

    @wraps(func)
    def wrapped(Q: Question):

        result = func(Q) # func itself can also raise NoSolution exception
        ans = Q.answer

        R, C = Q.A.shape
        if C == 0 and any(Q.b != 0):
            raise NoSolution(f'after {func.__name__}, no answer can equate nonzero b: b={Q.b}')

        assert Q.bounds.size == C , "design error"

        if Q.bounds.size > 0 and Q.bounds.sum() < Q.quota:
            raise NoSolution(f'after {func.__name__}, cannot reach quota from bound: sum({Q.bounds})={Q.bounds.sum()} < {Q.quota}')
        if np.any(ans._v > ans.quota):
            raise NoSolution(f'after {func.__name__}, answer out of quota: {ans._v}>{ans.quota}')



        return result

    return wrapped



#@debug
@raiseExceptionIfNotSolvableAfterwards
def reduce_col(Q: Question) -> None:
    R, C = Q.A.shape
    if C < 2: return

    d = defaultdict(list)
    enc = unique._encode(Q.A)  # [7,7,5,5,3,3,1]
    for category, loc in zip(enc, range(C)):
        d[category].append(loc)  # defaultdict(<class 'list'>, {7: [0, 1], 5: [2, 3], 3: [4, 5], 1: [6]})

    col_to_keep, col_to_drop, bounds_new = zip(*((locs[0], locs[1:], Q.bounds[locs].sum()) for category, locs in
                                                 d.items()))  # [(0, 2), (2, 2), (4, 2), (6, 1)]

    col_to_drop_in_A = list(chain(*col_to_drop))
    col_to_drop_in_ans = Q.answer.unknown_loc[col_to_drop_in_A]
    answer_new_v = fork.delete(Q.answer._v, col_to_drop_in_ans)
    answer_new_loc = fork.delete(Q.answer._loc, col_to_drop_in_ans)

    Q.A = Q.A[:, col_to_keep]
    Q.bounds = model.array(bounds_new)
    Q.answer = Answer(value=answer_new_v, location=answer_new_loc, len=len(Q.answer))


#@debug
@raiseExceptionIfNotSolvableAfterwards
def eliminate(Q: Question) -> None:
    R, C = Q.A.shape
    if C == 0: return
    Ae, be = gauss_elim.elim(Q.A, Q.b)
    Q.A, Q.b = Ae, be


#@debug
@raiseExceptionIfNotSolvableAfterwards
def zero_in_b(Q: Question) -> None:
    '''
    if element in bounds is 0, respective element in answer is 0
    '''
    #
    bounds.lower_upper_bound(Q.A, Q.b, Q.bounds)
    #
    ans: Answer = Q.answer
    val_unknown_locs = ans.unknown_loc
    assert np.array_equal(val_unknown_locs.shape, Q.bounds.shape)

    zbls = bounds.zero_bound_loc(Q.bounds)
    for zbl in zbls:
        zero_loc = val_unknown_locs[zbl]
        ans._v[zero_loc] = 0  # Q.answer updated in place
    _bound_new = fork.delete(Q.bounds, zbls)
    _A_new = fork.delete(Q.A, zbls, axis=1)
    Q.A, Q.bounds = _A_new, _bound_new



#@debug
@raiseExceptionIfNotSolvableAfterwards
def only_1_element_in_row(Q: Question):
    '''
    if only 1 element in a row r is non-zero, b[r] is the answer to respective element in answer
    :return proceed as bool
    '''
    #
    ans: Answer = Q.answer
    val_unknown_locs = ans.unknown_loc
    assert np.array_equal(val_unknown_locs.shape, Q.bounds.shape)

    #
    rcs = bounds.one_element_row_locs(Q.A)  # [(0,4), (1,2), (2,0)]
    if not rcs: return
    rs = [r for r, c in rcs]  # [0,1,2]
    cs = [c for r, c in rcs]  # [4,2,0]

    subA = Q.A[:, cs]
    subx = Q.b[rs]
    b_to_update = subA @ subx

    # check eligibility, dont assign/update Question until check
    for r, c in rcs:
        if Q.b[r] > Q.bounds[c]:
            raise NoSolution(f'{Q.b[r]} = Q.b[{r}] > Q.bounds[{c}] = {Q.bounds[c]}')

    if subx.sum() > Q.quota:
        raise NoSolution(f'sum({subx})={subx.sum()} > {Q.quota} = Q.quota')

    if np.any(b_to_update > Q.b):
        raise NoSolution(f'b_to_update={b_to_update} > {Q.b} = Q.b')

    # check done, update Question now
    # update answer, reduce quota
    for r, c in rcs:
        val_b_loc = val_unknown_locs[c]
        ans._v[val_b_loc] = Q.b[r]
        Q.quota -= Q.b[r] # because check above, Q.quota remains non-negative

    # update b, reduce bounds, reduce A
    Q.b -= b_to_update # because check above, Q.b remains non-negative
    Q.A = fork.delete(Q.A, cs, axis=1)
    Q.bounds = fork.delete(Q.bounds, cs)


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
        if np.any(new_b < 0): continue
        #
        new_ans: Answer = Q.answer.copy()
        ans_loc = ans_unknown_loc[minloc]
        new_ans._v[ans_loc] = q_used
        #
        yield Question(new_A.copy(), new_b, quota=q_rest, bounds=new_bound.copy(), ans=new_ans)

    # todo: delete Q?



def _fingerprint(Q: Question) -> tuple:
    '''everything Question.__eq__ compares, as raw bytes: much cheaper than copying Q to compare'''
    ans = Q.answer
    return (Q.A.shape, Q.A.tobytes(), Q.b.tobytes(), Q.bounds.tobytes(), Q.quota,
            ans._v.tobytes(), ans._loc.tobytes())


def solve_question(Q: Question)->Iterator[array]:
    stack = list()
    stack.append(Q)

    while stack:
        Q : Question = stack.pop()

        try:
            fp = _fingerprint(Q)
            while True:
                reduce_col(Q)
                eliminate(Q)
                zero_in_b(Q)
                only_1_element_in_row(Q)
                fp_new = _fingerprint(Q)
                if fp_new == fp:
                    break
                fp = fp_new

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
DEFAULT_DIVERSIFY = 0.0


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
          progress: Optional[Callable[[str], None]] = None, isomorph_free: bool = True,
          diversify: float = DEFAULT_DIVERSIFY):
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

    diversify is the probability that, instead of the most recently found partial
    matrix, a uniformly random pending one is extended next. Strict depth-first
    can spend ages exhausting one dead-end subtree while solutions sit in an
    unexplored sibling; occasional jumps cure that, and since every pending
    matrix is still extended eventually, exhaustive runs do the same work in a
    different order (the random choices are seeded, so runs are reproducible).

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
    stack = [srg]
    yielded = 0
    explored = 0
    rng = random.Random(0)

    def status() -> str:
        pending = defaultdict(int)
        for p in stack:
            pending[p._matrix.shape[0]] += 1
        rows = sorted(set(reached) | set(pending))
        per_row = ' '.join(f'{r}:{pending[r]}/{reached[r]}' for r in rows)
        return (f'explored {explored} partial matrices, {yielded} solutions, {time.time() - t_start:.0f}s elapsed; '
                f'pending/reached by rows built: {per_row}')

    while stack and (max_solutions is None or yielded < max_solutions):
        if diversify and len(stack) > 1 and rng.random() < diversify:
            j = rng.randrange(len(stack))
            stack[j], stack[-1] = stack[-1], stack[j]
        partial = stack.pop()
        explored += 1

        children = []
        for child in advance(partial):
            if child.solved():
                if _fresh(seen_done, child._matrix, isomorph_free):
                    yielded += 1
                    yield child._matrix.astype(model.dtype)  # API / database files stay int8 0/1
                    if max_solutions is not None and yielded >= max_solutions:
                        break
            elif spectral.feasible(child._matrix, spectrum) \
                    and _fresh(seen[child._matrix.shape[0]], child._matrix, isomorph_free):
                reached[child._matrix.shape[0]] += 1
                children.append(child)
        stack.extend(reversed(children))  # the first child is explored first

        if progress and time.time() - last >= PROGRESS_INTERVAL:
            last = time.time()
            progress(status())

    if progress:
        progress(('finished' if not stack else 'stopped at max_solutions') + ': ' + status())
