"""
Multi-process version of solver.solve: one Pool, created once, no nested pools.

The depth-first search is cut into time slices. A task is a list of partial matrices (subtree roots); a worker runs
the ordinary depth-first loop of solver.solve on them for ``SLICE_SECONDS`` and returns the solutions it found, plus
the part of its stack that it did not get to (siblings at every depth). The master puts those leftovers back on its
own stack (global depth-first order), then hands the next ones to whichever worker is free. Partial classes are
claimed before queuing; without shared claims the master deduplicates returned roots itself. Because
subtrees are wildly uneven, slicing keeps every core busy until the stack is empty, which static splitting of the
stack cannot do. The stack the master holds *is* a checkpoint of the whole search.

Workers share exact canonical keys through packed byte tables in a manager process. A claim stores only the
complete key plus an occupancy byte per allocated slot; there are no persistent per-key Python bytes objects,
(row, key) tuples, or ownership tokens. Hash collisions are resolved by comparing the full keys. No entries are
evicted, so the shared set rejects the same duplicate classes as the unbounded dictionary it replaces.
Worker-local sets are discarded after each time slice; complete solutions are deduplicated at the master.
"""
import json
import multiprocessing
import queue
import time
from collections import defaultdict
from typing import Callable, Optional

import numpy as np

from . import canon, solver, spectral
from .model import PartialSRG, SRGProperties
from .seen import SeenManager

SLICE_SECONDS = 20.0  # a worker hands back its stack after this long
FIRST_SLICE_SECONDS = 1.0  # the root is cut up quickly so that every worker has something to do

_spectra = {}  # per process cache of spectral.Spectrum


def _spectrum(vklu):
    if vklu not in _spectra:
        _spectra[vklu] = spectral.Spectrum(*vklu)
    return _spectra[vklu]


def _fresh_shared(local: set, shared, rows: int, matrix, isomorph_free: bool, counts=None) -> bool:
    """solver._fresh against the shared exact-key store: the first class claim wins."""
    if not isomorph_free:
        return True
    key = canon.canonical_key(matrix)
    if key is None:
        if counts is not None:
            counts[rows][1] += 1
        return True
    if key in local:
        if counts is not None:
            counts[rows][0] += 1
        return False
    local.add(key)
    return shared is None or shared.claim(rows, key)


def work(task):
    """Run the depth-first search from the given partial matrices for a time slice (in a worker process).

    task = (vklu, roots, seconds, isomorph_free). Returns (solutions, leftover, explored, cpu_seconds):
    leftover is the unexplored part of the stack in stack order (last = next to explore).
    """
    vklu, roots, seconds, isomorph_free, shared = task
    t0 = time.process_time()
    deadline = time.time() + seconds
    spectrum = _spectrum(vklu)
    seen = defaultdict(set)
    seen_done = set()
    counts = defaultdict(lambda: [0, 0])
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
                    and _fresh_shared(seen[rows], shared, rows, child._matrix, isomorph_free, counts):
                children.append(child)
        stack.extend(reversed(children))
    if shared is not None and counts:
        shared.record_local(dict(counts))
    return solutions, [p._matrix for p in stack], explored, time.process_time() - t0


worker_cpu_seconds = 0.0  # CPU time used by the workers of the last/running solve_parallel (the master's own is separate)


def solve_parallel(srg: PartialSRG, max_solutions: Optional[int] = solver.DEFAULT_MAX_SOLUTIONS,
                   progress: Optional[Callable[[str], None]] = None, isomorph_free: bool = True,
                   workers: Optional[int] = None, slice_seconds: float = SLICE_SECONDS, share_seen: bool = True,
                   dedup_progress: Optional[Callable[[dict], None]] = None):
    """Yield one solution per isomorphism class, using `workers` processes.

    Shared partial-key metrics are appended as JSON to progress lines and sent
    as dictionaries to dedup_progress, periodically and before manager shutdown.
    Metrics exclude complete-solution deduplication. With share_seen=False or
    isomorph_free=False they are unavailable (no dedup snapshot is emitted).
    Worker-local hit/skip counts lag until slices return; capped runs can omit
    counts from terminated slices. Exact storage/shared hits are sampled live.
    """
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

    snapshot = None

    def status() -> str:
        rows = sorted(set(reached) | set(pending))
        per_row = ' '.join(f'{r}:{pending[r]}/{reached[r]}' for r in rows)
        return (f'explored {explored} partial matrices, {yielded} solutions, {time.time() - t_start:.0f}s elapsed; '
                f'pending/reached by rows built: {per_row}'
                + ('; dedup: ' + json.dumps(snapshot, sort_keys=True) if snapshot is not None else ''))

    # 'spawn' on macOS: the worker function is importable, nothing is inherited
    ctx = multiprocessing.get_context()
    with SeenManager(ctx=ctx) as manager, ctx.Pool(workers) as pool:
        # the isomorphism classes reached so far, shared by all workers (a worker that finds one already claimed drops
        # it), so the parallel search expands about as many partial matrices as the serial one
        shared = manager.SharedSeen() if share_seen and isomorph_free else None
        def sample_dedup(state):
            nonlocal snapshot
            if shared is not None:
                snapshot = shared.stats()
                snapshot.update(elapsed_sec=time.time() - t_start, state=state,
                                local_counts_complete=not in_flight)
                if dedup_progress:
                    dedup_progress(snapshot)

        def submit():
            nonlocal in_flight
            while stack and in_flight < workers:
                m = stack.pop()
                pending[m.shape[0]] -= 1
                first = explored == 0 and in_flight == 0 and m.shape[0] == srg._matrix.shape[0]
                task = (vklu, [m], FIRST_SLICE_SECONDS if first else slice_seconds, isomorph_free, shared)
                pool.apply_async(work, (task,), callback=results.put, error_callback=results.put)
                in_flight += 1

        sample_dedup('started')
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
            if (progress or dedup_progress) and time.time() - last >= solver.PROGRESS_INTERVAL:
                last = time.time()
                sample_dedup('running')
                if progress:
                    progress(status())
        pool.terminate()
        pool.join()
        sample_dedup('finished' if not stack and not in_flight else 'stopped at max_solutions')
    if progress:
        progress(('finished' if not stack and not in_flight else 'stopped at max_solutions') + ': ' + status())
