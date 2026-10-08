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
import re
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


_STAT = re.compile(r'^(cpu_sec|wall_clock_sec) = (None|[0-9][0-9.eE+-]*)(?:  # (.*))?$', re.M)


def _hardware_short() -> str:
    '''the machine tag stored next to a performance number: CPU model and Python version'''
    try:
        cpu = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True).stdout.strip()
    except OSError:
        cpu = ''
    return f'{cpu or platform.processor() or platform.machine()}, python{platform.python_version()}'


def read_stats(path: str) -> dict:
    '''{'cpu_sec': (value or None, comment), 'wall_clock_sec': (...)} as stored in a problem file'''
    out = {'cpu_sec': (None, ''), 'wall_clock_sec': (None, '')}
    if os.path.exists(path):
        for name, value, comment in _STAT.findall(open(path).read()):
            out[name] = (None if value == 'None' else float(value), comment)
    return out


def _fmt_stat(x: float) -> str:
    return str(int(round(x))) if x >= 100 else f'{x:.4g}'


def merge_stats(old: dict, cpu_sec=None, wall_clock_sec=None, hardware: str = '') -> dict:
    '''
    Lazy update: a stored number is replaced only by a FASTER finished run (a smaller number); None means "not
    tackled", so any finished run replaces it. cpu_sec and wall_clock_sec are compared independently.
    '''
    new = {'cpu_sec': cpu_sec, 'wall_clock_sec': wall_clock_sec}
    out = {}
    for name, (value, comment) in old.items():
        if new[name] is not None and (value is None or new[name] < value):
            out[name] = (new[name], hardware)
        else:
            out[name] = (value, comment)
    return out


def _stat_lines(stats: dict) -> str:
    lines = []
    for name in ('cpu_sec', 'wall_clock_sec'):
        value, comment = stats[name]
        lines.append(f'{name} = None' if value is None else f'{name} = {_fmt_stat(value)}  # {comment}')
    return '\n'.join(lines) + '\n'


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


def note_attempt(v, k, l, u, text: str) -> None:
    """append a line to the docstring of an existing result file (e.g. a solver run that found nothing new)"""
    path = problem_path(v, k, l, u)
    src = open(path).read()
    if not src.startswith("'''"):
        return
    end = src.index("'''", 3)
    open(path, 'w').write(src[:end].rstrip('\n') + '\n' + text.strip('\n') + '\n' + src[end:])


def write_problem(v, k, l, u, matrices, notes: str, force: bool = False, perf: dict = None) -> str:
    '''
    Write problem_V_K_L_U.py. perf = {'cpu_sec', 'wall_clock_sec', 'hardware'} of a FINISHED solver run, or None: the
    stored cpu_sec / wall_clock_sec are replaced only by faster numbers (merge_stats), never by slower ones.
    A placeholder is replaced. A file that already holds a result is MERGED:
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
    merging = os.path.exists(path) and not force and not is_placeholder(path)
    if merging:
        from . import get_solutions
        existing = get_solutions(v, k, l, u)
    sols = standardize(list(existing) + list(matrices))
    if merging:
        # the file's old STATUS describes an older state: the new notes' STATUS replaces it (if they have one)
        old_lines = _docstring_body(path).split('\n')
        old_status = [ln for ln in old_lines if ln.startswith('STATUS:')]
        old_rest = [ln for ln in old_lines if not ln.startswith('STATUS:')]
        new_lines = doc.split('\n')
        new_status = [ln for ln in new_lines if ln.startswith('STATUS:')]
        new_rest = [ln for ln in new_lines if not ln.startswith('STATUS:')]
        status = (new_status or old_status or [''])[0]
        if new_status and existing:
            status += f' [the file now records {len(sols)} graph(s) in total, merged with its earlier results]'
        doc = '\n'.join(([status] if status else []) + old_rest + [''] + new_rest).strip('\n')
    for m in sols:
        assert SRGProperties.from_matrix(m).vklu == (v, k, l, u)
    body = ''.join(f'"""{codec.encode(m)}""",\n' for m in sols)
    if not sols:
        doc = 'no solution.\n' + doc
    stats = read_stats(path)
    if perf:
        stats = merge_stats(stats, perf.get('cpu_sec'), perf.get('wall_clock_sec'), perf.get('hardware', ''))
    with open(path, 'w') as f:
        f.write(f"'''\n{doc}\n'''\n"
                f"v, k, l, u = {v}, {k}, {l}, {u}\n"
                f"{_stat_lines(stats)}"
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
        # CPU seconds, not wall-clock: a process that is paused or starved by other jobs must not use up its budget
        if time_limit is not None and time.process_time() - c0 > time_limit:
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
        details = f'{_hardware()}\nsearch stopped after {elapsed:.0f}s without finishing; not a proof of non-existence'
        if is_placeholder(problem_path(v, k, l, u)):
            mark_status(v, k, l, u, f'tackled - UNDECIDED: no solution found within the {time_limit:g}s time limit', details)
        elif os.path.exists(problem_path(v, k, l, u)):  # a graph is already recorded (e.g. constructed): note the attempt
            note_attempt(v, k, l, u, f'solver attempt: found no graph within the {time_limit:g}s time limit '
                                     f'({cpu:.0f}s CPU, {elapsed:.0f}s wall-clock); this says nothing about existence\n{_hardware()}')
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
    notes = status + '\n'
    perf = None if stopped else dict(cpu_sec=cpu, wall_clock_sec=elapsed, hardware=_hardware_short())
    return write_problem(v, k, l, u, found, notes, force=force, perf=perf)


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
    if src:
        notes = (f'STATUS: derived - the complements of the {len(src)} graph(s) recorded in problem_{cv}_{ck}_{cl}_{cu}: the '
                 f'complement of an SRG({cv},{ck},{cl},{cu}) is an SRG({v},{k},{l},{u}) and vice versa, so this is exact and '
                 f'needs no search; it records as many graphs as its partner does\n')
    else:
        notes = (f'STATUS: derived - problem_{cv}_{ck}_{cl}_{cu} has no solution, and the complement of an '
                 f'SRG({v},{k},{l},{u}) would be an SRG({cv},{ck},{cl},{cu}), so this one does not exist either (exact, no search)\n')
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
