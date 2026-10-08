"""Status board of the builder runs: ``python -m srg.database status [logdir]``.

Reads the progress lines the solver prints to stderr (one ``*.err`` file per run in ``logdir``) and an optional
``queue.txt`` (one ``v k l u`` per line, in start order). For every quest it shows

    elapsed | pending partial matrices | graphs harvested so far / graphs expected

* elapsed: the last ``T s elapsed`` of the log (a snapshot; a run that is no longer alive shows its last value).
* pending: sum of the ``pending`` counters over all rows of the last progress line, i.e. partial matrices that are
  still to be propagated. 0 pending on a ``finished:`` line means the search is exhaustive.
* harvested: ``S solutions`` of the last line (graphs found so far, before the final merge/dedupe of the builder).
* expected: the number of graphs Brouwer's table gives, read from the problem file docstring (``exists (N graphs)``;
  0 when it does not exist; ``?`` when the table gives no count).
"""
import re
import subprocess
from pathlib import Path

_LINE = re.compile(r'\[srg (\d+),(\d+),(\d+),(\d+)\] (finished: )?explored (\d+) partial matrices, (\d+) solutions, '
                   r'(\d+)s elapsed; pending/reached by rows built: (.*)')


def expected(v, k, l, u):
    """Number of graphs Brouwer lists for the quest, as a string."""
    f = Path(__file__).with_name(f'problem_{v}_{k}_{l}_{u}.py')
    if not f.exists():
        return '?'
    head = f.read_text().split('\nv, k, l, u')[0]
    if 'does not exist' in head:
        return '0'
    m = re.search(r'exists \((\d+) graphs?\)', head)
    if m:
        return m.group(1)
    return 'many' if 'many graphs' in head else '?'


def last_status(err: Path):
    """The last progress line of a log as a dict, or None."""
    last = None
    for line in err.read_text(errors='replace').splitlines():
        m = _LINE.match(line)
        if m:
            last = m
    if last is None:
        return None
    v, k, l, u, fin, explored, sols, secs, rows = last.groups()
    pending = sum(int(p.split('/')[0]) for p in re.findall(r'\d+:(\d+/\d+)', rows))
    return dict(quest=tuple(map(int, (v, k, l, u))), finished=bool(fin), explored=int(explored),
                solutions=int(sols), elapsed=int(secs), pending=pending)


def _alive(quest):
    out = subprocess.run(['pgrep', '-fl', 'srg.database build ' + ' '.join(map(str, quest))],
                         capture_output=True, text=True).stdout
    return any('pgrep' not in line for line in out.splitlines())


def _hms(sec):
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f'{h}h{m:02d}m{s:02d}s' if h else f'{m}m{s:02d}s'


def report(logdir):
    logdir = Path(logdir)
    rows, seen = [], set()
    for err in sorted(logdir.glob('*.err')):
        st = last_status(err)
        if st is None or st['quest'] in seen:
            continue
        seen.add(st['quest'])
        state = 'finished' if st['finished'] and st['pending'] == 0 else 'running' if _alive(st['quest']) else 'stopped'
        rows.append((state, st))
    queue = []
    q = logdir / 'queue.txt'
    if q.exists():
        for line in q.read_text().splitlines():
            parts = line.split()
            if len(parts) == 4 and tuple(map(int, parts)) not in seen:
                queue.append(tuple(map(int, parts)))
    lines = [f'{"quest":<17}{"state":<10}{"elapsed":>10}  {"pending":>8}  {"harvested":>9}  {"expected":>8}']
    for state, st in rows:
        v, k, l, u = st['quest']
        lines.append(f'SRG({v},{k},{l},{u})'.ljust(17) + f'{state:<10}{_hms(st["elapsed"]):>10}  {st["pending"]:>8}  '
                     f'{st["solutions"]:>9}  {expected(v, k, l, u):>8}')
    for n, (v, k, l, u) in enumerate(queue, 1):
        lines.append(f'SRG({v},{k},{l},{u})'.ljust(17) + f'{"queued #" + str(n):<10}{"-":>10}  {"-":>8}  {"-":>9}  '
                     f'{expected(v, k, l, u):>8}')
    return '\n'.join(lines)
