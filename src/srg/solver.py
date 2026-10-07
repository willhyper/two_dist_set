#!python
#cython: language_level=3

import json
import os
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

    s = model.zeros((2, v))
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
    answer_new_v = np.delete(Q.answer._v, col_to_drop_in_ans)
    answer_new_loc = np.delete(Q.answer._loc, col_to_drop_in_ans)

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
    _bound_new = np.delete(Q.bounds, zbls)
    _A_new = np.delete(Q.A, zbls, axis=1)
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
    Q.A = np.delete(Q.A, cs, axis=1)
    Q.bounds = np.delete(Q.bounds, cs)


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
    new_bound = np.delete(Q.bounds, minloc)
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



def solve_question(Q: Question)->Iterator[array]:
    stack = list()
    stack.append(Q)

    while stack:
        Q : Question = stack.pop()

        try:
            while True:
                Qdummy = Q.copy()
                reduce_col(Q)
                eliminate(Q)
                zero_in_b(Q)
                only_1_element_in_row(Q)
                if Q == Qdummy:
                    break

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

PROGRESS_INTERVAL = 5.0  # seconds between progress lines within a level


def _unique(matrices: list) -> list:
    '''one matrix per isomorphism class (matrices too symmetric to canonize are all kept)'''
    kept, seen = [], set()
    for p in matrices:
        key = canon.canonical_key(p._matrix)
        if key is not None:
            if key in seen:
                continue
            seen.add(key)
        kept.append(p)
    return kept


def _prune(partials: list, r: float, s: float, isomorph_free: bool) -> list:
    '''
    drop partial matrices that provably cannot be completed (eigenvalue
    interlacing, see spectral.py), and - if isomorph_free - all but one of
    each isomorphism class (see canon.py): isomorphic partial matrices have
    the same completions, so searching one representative loses nothing.
    '''
    kept, seen = [], set()
    for p in partials:
        if not spectral.feasible(p._matrix, r, s):
            continue
        if isomorph_free:
            key = canon.canonical_key(p._matrix)
            if key is not None:
                if key in seen:
                    continue
                seen.add(key)
        kept.append(p)
    return kept


# Bump when a change to the search alters what a checkpoint means (the order
# or content of a level's frontier), so stale checkpoints are not resumed.
CHECKPOINT_VERSION = 1
CHECKPOINT_INTERVAL = 60.0  # seconds between checkpoints within a level


def _stack(matrices: list, rows: int, cols: int) -> np.ndarray:
    return np.stack(matrices) if matrices else model.zeros((0, rows, cols))


def _save_checkpoint(path: str, meta: dict, frontier: list, i: int, grown: list, found: list,
                     elapsed: float, finished: bool) -> None:
    '''
    atomically write the search state: the partial matrices still to advance
    (frontier, of which the first i are already advanced), the candidates they
    produced so far (grown) and every solution found so far. Plain arrays plus
    JSON, no pickle, so loading a file can never run code.
    '''
    v = meta['vklu'][0]
    R = frontier[0]._matrix.shape[0] if frontier else v
    state = dict(meta, i=i, elapsed=elapsed, finished=finished, version=CHECKPOINT_VERSION)
    tmp = path + '.tmp'
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(tmp, 'wb') as f:
        np.savez_compressed(f, state=np.array(json.dumps(state)),
                            frontier=_stack([p._matrix for p in frontier], R, v),
                            grown=_stack([p._matrix for p in grown], R + 1, v),
                            found=_stack(found, v, v))
    os.replace(tmp, path)


def _load_checkpoint(path: str, meta: dict):
    '''(frontier, i, grown, found, elapsed, finished), or None if there is no usable checkpoint'''
    if not path or not os.path.exists(path):
        return None
    with np.load(path, allow_pickle=False) as z:
        state = json.loads(str(z['state']))
        if state.get('version') != CHECKPOINT_VERSION or any(state.get(k) != v for k, v in meta.items()):
            return None
        frontier = [PartialSRG(m) for m in z['frontier']]
        grown = [PartialSRG(m) for m in z['grown']]
        found = list(z['found'])
    return frontier, state['i'], grown, found, state['elapsed'], state['finished']


def solve(srg: PartialSRG, max_solutions: Optional[int] = DEFAULT_MAX_SOLUTIONS,
          progress: Optional[Callable[[str], None]] = None, isomorph_free: bool = True,
          checkpoint: Optional[str] = None):
    '''
    yields completed adjacency matrices, level by level (breadth-first over
    partially-built rows), stopping once max_solutions have been yielded -
    this only settles existence quickly instead of paying to enumerate every
    symmetry of a solution-rich quest. Pass max_solutions=None to disable the
    cap and enumerate exhaustively.

    Every level is pruned with eigenvalue interlacing and, unless
    isomorph_free=False, reduced to one partial matrix per isomorphism class,
    so the matrices yielded are representatives, not every vertex-labeling of
    each solution.

    progress, if given, is called with a one-line status string at the start
    and end of every level and every PROGRESS_INTERVAL seconds within one.

    checkpoint, if given, is a file path: the search state is saved there at
    the end of every level and every CHECKPOINT_INTERVAL seconds within one,
    and if the file already holds a checkpoint of the same quest (same
    parameters, cap and mode) the search resumes from it instead of from
    scratch - including yielding the solutions found before it. A checkpoint
    of a finished search just replays its solutions.
    '''
    t_start = time.time()
    v, k, l, u = SRGProperties.from_matrix(srg._matrix).vklu
    r, s = spectral.eigen_rs(v, k, l, u)
    meta = dict(vklu=[int(x) for x in (v, k, l, u)], max_solutions=max_solutions, isomorph_free=isomorph_free)

    frontier, i, grown, found, elapsed0, finished = [srg], 0, [], [], 0.0, False
    resumed = _load_checkpoint(checkpoint, meta)
    if resumed:
        frontier, i, grown, found, elapsed0, finished = resumed
        if progress:
            progress(f'resumed from {checkpoint}: {"finished, " if finished else ""}{len(found)} solutions so far, '
                     f'{len(frontier)} partial matrices (row {frontier[0]._matrix.shape[0] + 1 if frontier else v}'
                     f', {i} advanced), {elapsed0:.0f}s already computed')

    def elapsed() -> float:
        return elapsed0 + time.time() - t_start

    def save(finished_now: bool = False):
        if checkpoint:
            _save_checkpoint(checkpoint, meta, frontier, i, grown, found, elapsed(), finished_now)

    yield from found  # solutions from before the checkpoint
    while frontier and (max_solutions is None or len(found) < max_solutions):
        row = frontier[0]._matrix.shape[0] + 1  # the row being built
        t_level = last = last_save = time.time()
        if progress:
            progress(f'row {row}/{v}: {len(frontier)} partial matrices to advance'
                     + (f' ({i} already advanced)' if i else ''))

        while i < len(frontier):
            grown += advance(frontier[i])
            i += 1
            now = time.time()
            if progress and now - last >= PROGRESS_INTERVAL:
                last = now
                progress(f'row {row}: advanced {i}/{len(frontier)}, {len(grown)} candidates, '
                         f'{elapsed():.0f}s elapsed')
            if checkpoint and now - last_save >= CHECKPOINT_INTERVAL:
                last_save = now
                save()

        lst_done, lst_undone = partition_by_done(grown)
        if isomorph_free:
            lst_done = _unique(lst_done)
        n_grown, n_done = len(grown), len(lst_done)
        new_found = [p._matrix for p in lst_done]
        if max_solutions is not None:
            new_found = new_found[:max_solutions - len(found)]
        found += new_found
        frontier, i, grown = _prune(lst_undone, r, s, isomorph_free), 0, []
        if progress:
            progress(f'row {row} done: {len(frontier)} kept of {n_grown} candidates '
                     f'({n_done} solved), level {time.time() - t_level:.1f}s, '
                     f'{elapsed():.0f}s elapsed')
        save(finished_now=not frontier)
        yield from new_found

    if checkpoint and not finished:
        frontier = []  # capped out: nothing left to resume
        save(finished_now=True)
