'''
Build / extend the problem database: solve a quest and write problem_V_K_L_U.py.

    python -m srg.database build v k l u [max_solutions]   # solve (resumable) and write the file
    python -m srg.database complement v k l u              # derive from the quest's complement

Every matrix is checked with PartialSRG.solved() and standardized with
canon.canonical_matrix before it is written, so a file lists one matrix per
isomorphism class, in a canonical form that does not depend on the search.
'''
import os
import platform
import subprocess
import sys

import numpy as np

from .. import canon, solver
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


def _format_matrix(m: np.ndarray) -> str:
    text = np.array2string(m, separator=', ', threshold=sys.maxsize, max_line_width=10 ** 6)
    pad = ' ' * len('solutions: list = [array(')
    return 'array(' + text.replace('\n', '\n' + pad).replace('[[', '[[', 1) + ')'


def standardize(matrices) -> list:
    '''one canonical-form matrix per isomorphism class, in a deterministic order'''
    by_key = {}
    for m in matrices:
        assert PartialSRG(m).solved(), 'refusing to record a matrix that is not a complete SRG'
        c = canon.canonical_matrix(m)
        by_key.setdefault(c.tobytes(), c)
    return [by_key[k] for k in sorted(by_key)]


def write_problem(v, k, l, u, matrices, notes: str, force: bool = False) -> str:
    path = problem_path(v, k, l, u)
    if os.path.exists(path) and not force:
        raise FileExistsError(f'{path} exists; pass force=True to overwrite')
    sols = standardize(matrices)
    for m in sols:
        assert SRGProperties.from_matrix(m).vklu == (v, k, l, u)
    body = ',\n                         '.join(_format_matrix(m) for m in sols)
    doc = notes.strip('\n')
    if not sols:
        doc = 'no solution.\n' + doc
    with open(path, 'w') as f:
        f.write(f"'''\n{doc}\n'''\n"
                f"from srg.model import array\n\n"
                f"v, k, l, u = {v}, {k}, {l}, {u}\n"
                f"solutions: list = [{body}]\n")
    return path


def build(v, k, l, u, max_solutions=solver.DEFAULT_MAX_SOLUTIONS, force=False) -> str:
    '''solve (checkpointed, so an interrupted build resumes) and write the problem file'''
    assert SRGProperties(v, k, l, u).is_srg(), f'{(v, k, l, u)} do not form an SRG'
    ckpt = f'.srg_checkpoints/srg_{v}_{k}_{l}_{u}_max{max_solutions}.npz'

    resumed = []

    def progress(msg):
        if msg.startswith('resumed'):
            resumed.append(msg)
        print(f'[srg {v},{k},{l},{u}] {msg}', file=sys.stderr, flush=True)

    found = list(solver.solve(PartialSRG(solver._seed(v, k, l, u)), max_solutions=max_solutions,
                              progress=progress, checkpoint=ckpt))
    with np.load(ckpt, allow_pickle=False) as z:
        import json
        elapsed = json.loads(str(z['state']))['elapsed']  # total compute time across resumed runs
    n = len(standardize(found))
    notes = (f'{_hardware()}\n'
             f'{elapsed:.4g}s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process'
             f'{" (total compute time across resumed runs)" if resumed else ""}\n')
    if n >= max_solutions:
        notes += f'{n} isomorphism classes listed: search was capped at max_solutions={max_solutions}, more may exist\n'
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
    notes = (f'complement of problem_{cv}_{ck}_{cl}_{cu}: the complement of an SRG({cv},{ck},{cl},{cu}) is an '
             f'SRG({v},{k},{l},{u}) and vice versa, so its solutions are exactly the complements of that '
             f'problem\'s. No search was run.\n')
    return write_problem(v, k, l, u, mats, notes, force=force)
