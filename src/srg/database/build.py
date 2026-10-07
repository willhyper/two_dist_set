'''
Build / extend the problem database: solve a quest and write problem_V_K_L_U.py.

    python -m srg.database build v k l u [max_solutions]   # solve (resumable) and write the file
    python -m srg.database complement v k l u              # derive from the quest's complement

Every matrix is checked with PartialSRG.solved() and standardized with
canon.canonical_matrix before it is written, so a file lists one matrix per
isomorphism class, in a canonical form that does not depend on the search.
'''
import inspect
import json
import os
import platform
import subprocess
import sys
import time

import numpy as np

from .. import canon, solver
from . import codec
from ..model import PartialSRG, SRGProperties

HERE = os.path.dirname(os.path.abspath(__file__))


def problem_path(v, k, l, u) -> str:
    return os.path.join(HERE, f'problem_{v}_{k}_{l}_{u}.py')


def complement_vklu(v, k, l, u) -> tuple:
    return v, v - k - 1, v - 2 - 2 * k + u, v - 2 * k + l


def _hardware() -> str:
    try:
        cpu = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True).stdout.strip()
        ncpu = subprocess.run(['sysctl', '-n', 'hw.ncpu'], capture_output=True, text=True).stdout.strip()
        cpu = f'{cpu} ({ncpu} cores)' if cpu else platform.processor()
    except OSError:
        cpu = platform.processor() or platform.machine()
    return f'{cpu}, {platform.system()} {platform.mac_ver()[0] or platform.release()}, python{platform.python_version()}'


def standardize(matrices) -> list:
    '''one canonical-form matrix per isomorphism class, in a deterministic order'''
    by_key = {}
    for m in matrices:
        assert PartialSRG(m).solved(), 'refusing to record a matrix that is not a complete SRG'
        c = canon.canonical_matrix(m)
        by_key.setdefault(c.tobytes(), c)
    return [by_key[k] for k in sorted(by_key)]


def is_placeholder(path: str) -> bool:
    '''a problem file that only records a status (todo / undecided), not a result'''
    if not os.path.exists(path):
        return False
    with open(path) as f:
        head = f.read(4000)
    return "\nstatus = '" in head


def mark_status(v, k, l, u, status: str, details: str = '') -> None:
    '''rewrite the STATUS line (and add details) of a placeholder problem file'''
    path = problem_path(v, k, l, u)
    if not is_placeholder(path):
        return
    lines = open(path).read().split('\n')
    for i, line in enumerate(lines):
        if line.startswith('STATUS:'):
            lines[i] = 'STATUS: ' + status + ('\n' + details.strip('\n') if details else '')
            break
    text = '\n'.join(lines)
    text = text.replace("status = 'todo'", "status = 'undecided'") if status.startswith('tackled') else text
    open(path, 'w').write(text)


def _docstring_body(path: str) -> str:
    '''text inside the leading docstring of a problem file ('' if it has none)'''
    src = open(path).read()
    if not src.startswith("'''"):
        return ''
    return src[3:src.index("'''", 3)].strip('\n')


def write_problem(v, k, l, u, matrices, notes: str, force: bool = False) -> str:
    '''
    Write problem_V_K_L_U.py. A placeholder is replaced. A file that already holds a result is MERGED:
    its solutions are kept (one matrix per isomorphism class), the new matrices are added, and notes
    are appended to its docstring - unless force=True, which overwrites it.
    '''
    path = problem_path(v, k, l, u)
    doc = notes.strip('\n')
    existing = []
    if is_placeholder(path):
        # keep what the placeholder says about the table (verdict, comments, complement), drop its old STATUS
        kept = [ln for ln in _docstring_body(path).split('\n') if not ln.startswith('STATUS:')]
        doc = '\n'.join([doc] + kept).strip('\n')
    if os.path.exists(path) and not force and not is_placeholder(path):
        from . import get_solutions
        existing = get_solutions(v, k, l, u)
        doc = (_docstring_body(path) + '\n\n' + doc).strip('\n')
    sols = standardize(list(existing) + list(matrices))
    for m in sols:
        assert SRGProperties.from_matrix(m).vklu == (v, k, l, u)
    body = ''.join(f'"""{codec.encode(m)}""",\n' for m in sols)
    if not sols:
        doc = 'no solution.\n' + doc
    with open(path, 'w') as f:
        f.write(f"'''\n{doc}\n'''\n"
                f"v, k, l, u = {v}, {k}, {l}, {u}\n"
                f"solutions: list[str] = [\n{body}]\n")
    return path


class TimeLimit(Exception): pass


def build(v, k, l, u, max_solutions=solver.DEFAULT_MAX_SOLUTIONS, force=False, time_limit=None):
    '''
    solve and write the problem file. If solve() supports checkpoints the search
    is checkpointed, so an interrupted build resumes where it left off.
    '''
    assert SRGProperties(v, k, l, u).is_srg(), f'{(v, k, l, u)} do not form an SRG'
    resumable = 'checkpoint' in inspect.signature(solver.solve).parameters
    ckpt = f'.srg_checkpoints/srg_{v}_{k}_{l}_{u}_max{max_solutions}.npz'
    kwargs = dict(checkpoint=ckpt) if resumable else {}
    resumed = []

    def progress(msg):
        if msg.startswith('resumed'):
            resumed.append(msg)
        print(f'[srg {v},{k},{l},{u}] {msg}', file=sys.stderr, flush=True)

    t0, c0 = time.time(), time.process_time()

    def progress_limited(msg):
        progress(msg)
        if time_limit is not None and time.time() - t0 > time_limit:
            raise TimeLimit

    found, stopped = [], False
    try:
        for m in solver.solve(PartialSRG(solver._seed(v, k, l, u)), max_solutions=max_solutions,
                              progress=progress_limited, **kwargs):
            found.append(m)
    except TimeLimit:
        stopped = True
    elapsed, cpu = time.time() - t0, time.process_time() - c0
    if stopped and not found:
        # not a proof of anything: do not write a 'no solution' file
        print(f'[srg {v},{k},{l},{u}] undecided: no solution found within {time_limit}s', file=sys.stderr, flush=True)
        mark_status(v, k, l, u, f'tackled - UNDECIDED: no solution found within the {time_limit:g}s time limit',
                    f'{_hardware()}\nsearch stopped after {elapsed:.0f}s without finishing; not a proof of non-existence')
        return None
    if resumable:
        with np.load(ckpt, allow_pickle=False) as z:
            elapsed = json.loads(str(z['state']))['elapsed']  # total compute time across resumed runs
    n = len(standardize(found))
    if stopped:
        status = (f'STATUS: partially tackled - {n} graph(s) found; the search hit the {time_limit:g}s time limit before '
                  f'finishing, so more graphs may exist')
    elif n >= max_solutions:
        status = f'STATUS: tackled - stopped at the cap of {max_solutions} graphs; more may exist'
    elif n:
        status = f'STATUS: tackled - the search finished: these {n} graph(s) are ALL of them'
    else:
        status = 'STATUS: tackled - the search finished and found no solution'
    notes = (f'{status}\n{_hardware()}\n'
             f'{cpu:.4g}s CPU ({elapsed:.4g}s wall-clock). isomorph rejection + eigenvalue interlacing pruning, pure python, single process'
             f'{" (total compute time across resumed runs)" if resumed else ""}\n')
    return write_problem(v, k, l, u, found, notes, force=force)


def derive_complement(v, k, l, u, force=False) -> str:
    '''write problem(v,k,l,u) from the stored solutions of its complement problem'''
    from . import get_solutions
    cv, ck, cl, cu = complement_vklu(v, k, l, u)
    src = get_solutions(cv, ck, cl, cu)
    mats = []
    for m in src:
        c = 1 - m
        np.fill_diagonal(c, 0)
        mats.append(c.astype(m.dtype))
    notes = (f'STATUS: derived - the complements of the {len(src)} graph(s) recorded in problem_{cv}_{ck}_{cl}_{cu}: the '
             f'complement of an SRG({cv},{ck},{cl},{cu}) is an SRG({v},{k},{l},{u}) and vice versa, so this is exact and '
             f'needs no search; it records as many graphs as its partner does\n')
    return write_problem(v, k, l, u, mats, notes, force=force)


def construct(v, k, l, u) -> str:
    '''
    record graphs written down from a known construction (utils.constructions, e.g. Paley(q)) in the
    problem file. They are verified with solved() and standardized like solver results, but the
    docstring says they were NOT found by the search. Returns the path, or None if no construction
    is known for these parameters.
    '''
    from .. import utils
    found = utils.constructions(v, k, l, u)
    if not found:
        return None
    for name, m in found:
        assert PartialSRG(m).solved(), f'{name} is not an SRG({v},{k},{l},{u})'
    names = ', '.join(sorted({n for n, _ in found}))
    path = problem_path(v, k, l, u)
    if not is_placeholder(path) and os.path.exists(path):
        from . import get_solutions
        have = {canon.canonical_key(m, 10 ** 7) for m in get_solutions(v, k, l, u)}
        new = [m for _, m in found if canon.canonical_key(m, 10 ** 7) not in have]
        if not new:
            return None  # every constructed graph is already recorded: leave the file alone
        notes = (f'known construction ({names}) generated, checked with solved(), and added: it is a graph this file '
                 f'did not have yet (NOT found by the solver)')
        return write_problem(v, k, l, u, new, notes)
    # a placeholder: write_problem keeps what it says about the table and replaces its STATUS line
    status = (f'STATUS: constructed - graph(s) recorded from a known construction ({names}); the solver has NOT '
              f'found a solution for this quest itself yet, and the table may list more graphs than are recorded here')
    return write_problem(v, k, l, u, [m for _, m in found], status)
