"""
Multi-process version of solver.solve: one Pool, created once, no nested pools.

The depth-first search is cut into time slices. A task is a list of partial matrices (subtree roots); a worker runs
the ordinary depth-first loop of solver.solve on them for ``SLICE_SECONDS`` and returns the solutions it found, plus
the part of its stack that it did not get to (siblings at every depth). The master puts those leftovers back on its
own stack (global depth-first order, so memory stays small), drops the ones whose isomorphism class it has already
sent out (one global ``seen`` per number of rows), and hands the next ones to whichever worker is free. Because
subtrees are wildly uneven, slicing keeps every core busy until the stack is empty, which static splitting of the
stack cannot do. The stack the master holds *is* a checkpoint of the whole search.

What is lost against the serial search: workers do not share ``seen``, so two workers can rebuild the same
isomorphic subtree below their roots (wasted work, not wrong answers; solutions are de-duplicated by
canon.canonical_key at the master). Completeness is unchanged: every partial matrix that is not extended is either
infeasible (spectral), isomorphic to one that is, or already extended.
"""
import multiprocessing
import queue
import time
from collections import defaultdict
from typing import Callable, Optional

import numpy as np

from . import canon, solver, spectral
from .model import PartialSRG, SRGProperties

SLICE_SECONDS = 20.0  # a worker hands back its stack after this long
FIRST_SLICE_SECONDS = 1.0  # the root is cut up quickly so that every worker has something to do

_spectra = {}  # per process cache of spectral.Spectrum


def _spectrum(vklu):
    if vklu not in _spectra:
        _spectra[vklu] = spectral.Spectrum(*vklu)
    return _spectra[vklu]


def _fresh_shared(local: set, shared, token, rows: int, matrix, isomorph_free: bool) -> bool:
    """solver._fresh against a dict shared by all workers: the first process to claim an isomorphism class wins."""
    if not isomorph_free:
        return True
    key = canon.canonical_key(matrix)
    if key is None:
        return True
    if key in local:
        return False
    local.add(key)
    return shared is None or shared.setdefault((rows, key), token) == token


_slices = 0


def work(task):
    """Run the depth-first search from the given partial matrices for a time slice (in a worker process).

    task = (vklu, roots, seconds, isomorph_free). Returns (solutions, leftover, explored, cpu_seconds):
    leftover is the unexplored part of the stack in stack order (last = next to explore).
    """
    global _slices
    vklu, roots, seconds, isomorph_free, shared = task
    _slices += 1
    token = (multiprocessing.current_process().pid, _slices)
    t0 = time.process_time()
    deadline = time.time() + seconds
    spectrum = _spectrum(vklu)
    seen = defaultdict(set)
    seen_done = set()
    stack = [PartialSRG(m) for m in reversed(roots)]  # roots[0] is explored first
    solutions, explored = [], 0
    while stack and time.time() < deadline:
        partial = stack.pop()
        explored += 1
        children = []
        for child in solver.advance(partial):
            rows = child._matrix.shape[0]
            if child.solved():
                if solver._fresh(seen_done, child._matrix, isomorph_free):
                    solutions.append(child._matrix)
            elif spectral.feasible(child._matrix, spectrum) \
                    and _fresh_shared(seen[rows], shared, token, rows, child._matrix, isomorph_free):
                children.append(child)
        stack.extend(reversed(children))
    return solutions, [p._matrix for p in stack], explored, time.process_time() - t0


worker_cpu_seconds = 0.0  # CPU time used by the workers of the last/running solve_parallel (the master's own is separate)


def solve_parallel(srg: PartialSRG, max_solutions: Optional[int] = solver.DEFAULT_MAX_SOLUTIONS,
                   progress: Optional[Callable[[str], None]] = None, isomorph_free: bool = True,
                   workers: Optional[int] = None, slice_seconds: float = SLICE_SECONDS, share_seen: bool = True):
    """Same contract as solver.solve (yields one matrix per isomorphism class of solution), on `workers` processes."""
    global worker_cpu_seconds
    worker_cpu_seconds = 0.0
    workers = workers or multiprocessing.cpu_count()
    vklu = SRGProperties.from_matrix(srg._matrix).vklu
    t_start = last = time.time()

    seen = defaultdict(set)  # rows built -> classes already handed out
    seen_done = set()
    reached = defaultdict(int)
    pending = defaultdict(int)  # rows built -> matrices on the master's stack
    stack = [srg._matrix]
    pending[srg._matrix.shape[0]] += 1
    in_flight = 0
    explored = yielded = 0
    results = queue.Queue()

    def status() -> str:
        rows = sorted(set(reached) | set(pending))
        per_row = ' '.join(f'{r}:{pending[r]}/{reached[r]}' for r in rows)
        return (f'explored {explored} partial matrices, {yielded} solutions, {time.time() - t_start:.0f}s elapsed; '
                f'pending/reached by rows built: {per_row}')

    # 'spawn' on macOS: the worker function is importable, nothing is inherited
    ctx = multiprocessing.get_context()
    with ctx.Manager() as manager, ctx.Pool(workers) as pool:
        # the isomorphism classes reached so far, shared by all workers (a worker that finds one already claimed drops
        # it), so the parallel search expands about as many partial matrices as the serial one
        shared = manager.dict() if share_seen and isomorph_free else None
        def submit():
            nonlocal in_flight
            while stack and in_flight < workers:
                m = stack.pop()
                pending[m.shape[0]] -= 1
                first = explored == 0 and in_flight == 0 and m.shape[0] == srg._matrix.shape[0]
                task = (vklu, [m], FIRST_SLICE_SECONDS if first else slice_seconds, isomorph_free, shared)
                pool.apply_async(work, (task,), callback=results.put, error_callback=results.put)
                in_flight += 1

        submit()
        while in_flight and (max_solutions is None or yielded < max_solutions):
            try:
                res = results.get(timeout=1.0)
            except queue.Empty:
                res = None
            if res is not None:
                in_flight -= 1
                if isinstance(res, BaseException):
                    raise res
                solutions, leftover, n, cpu = res
                explored += n
                worker_cpu_seconds += cpu
                for m in solutions:
                    if solver._fresh(seen_done, m, isomorph_free):
                        yielded += 1
                        yield m
                        if max_solutions is not None and yielded >= max_solutions:
                            break
                for m in leftover:  # stack order: the last one is explored first
                    rows = m.shape[0]
                    # with shared seen the worker already claimed the class; otherwise claim it here
                    if shared is not None or solver._fresh(seen[rows], m, isomorph_free):
                        reached[rows] += 1
                        stack.append(m)
                        pending[rows] += 1
                submit()
            if progress and time.time() - last >= solver.PROGRESS_INTERVAL:
                last = time.time()
                progress(status())
        pool.terminate()
    if progress:
        progress(('finished' if not stack and not in_flight else 'stopped at max_solutions') + ': ' + status())
