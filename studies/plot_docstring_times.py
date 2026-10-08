'''
Scatter plot of the run times recorded in the problem_*.py docstrings: x = k (linear), y = seconds (log).

Two kinds of time are told apart, because they differ a lot when the machine was shared or a process was paused:
  CPU time   '2834s CPU (4181s wall-clock)', and the 'same session pure python: X s' of the Cython comparison
             (that benchmark used process_time)
  wall time  '(4181s wall-clock)', '3276s wall-clock.', and the unlabeled 'X s. isomorph rejection ...' lines of the
             earlier benchmarks and builder runs (they used a wall clock), plus 'totally elapsed' of the first 28,12,6,4 run
Filled markers are runs that finished (found everything / proved the answer); open markers are runs that were stopped by a
time limit without a final answer, so their true time is higher. Timings come from different code versions (the files keep
their whole history) and the Apple M1 numbers of the original author are left out (another machine).

Run:  python studies/plot_docstring_times.py out.png [out.csv]   (the csv lists every timing that was parsed)
'''
import csv
import glob
import os
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

NUM = r'([\d][\d,]*\.?\d*(?:e[+-]?\d+)?)'


def num(s):
    return float(s.replace(',', ''))


def parse(path):
    '''records [(kind 'cpu'|'wall', seconds, finished, pair_id)] from one problem file docstring'''
    src = open(path).read()
    if not src.startswith("'''"):
        return None, []
    doc = src[3:src.index("'''", 3)]
    lines = doc.split('\n')
    status = next((l for l in lines if l.startswith('STATUS:')), '')
    finished_status = not re.search(r'partially tackled|UNDECIDED|stopped by a|hit the .*time limit', status + ' ' + doc)
    recs, pid = [], 0
    skip_m1 = False
    for line in lines:
        if 'Apple M1' in line:
            skip_m1 = True  # the author's old timings on another machine follow
            continue
        if skip_m1:
            if re.match(r'^\s*[\d.]+s?\.?\s', line) or 'multi-' in line:
                continue
            skip_m1 = False
        m = re.match(rf'^{NUM}s CPU \({NUM}s wall-clock\)', line)
        if m:
            pid += 1
            recs += [('cpu', num(m.group(1)), finished_status, pid), ('wall', num(m.group(2)), finished_status, pid)]
            continue
        m = re.match(rf'^{NUM}s wall-clock\.', line)
        if m:
            recs.append(('wall', num(m.group(1)), finished_status, 0))
            continue
        m = re.match(rf'^{NUM}s\. cythonized.*same session pure python: {NUM}s', line)
        if m:
            recs.append(('cpu', num(m.group(2)), True, 0))
            continue
        m = re.match(rf'^{NUM}s\. isomorph rejection', line)
        if m:
            recs.append(('wall', num(m.group(1)), finished_status, 0))
            continue
        m = re.match(rf'^totally elapsed {NUM} s', line)
        if m:
            recs.append(('wall', num(m.group(1)), True, 0))
            continue
        m = re.match(rf'^search stopped after {NUM}s without finishing', line)
        if m:
            recs.append(('wall', num(m.group(1)), False, 0))
            continue
        m = re.search(rf'found no graph within the [\d.]+s time limit \({NUM}s wall-clock', line)
        if m:
            recs.append(('wall', num(m.group(1)), False, 0))
            continue
        m = re.search(rf'It received only ~{NUM}s', line)
        if m:
            recs.append(('cpu', num(m.group(1)), False, 0))
    return status, recs


def main():
    out = sys.argv[1]
    rows = []
    for p in sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'src', 'srg', 'database', 'problem_*.py'))):
        v, k, l, u = map(int, re.search(r'problem_(\d+)_(\d+)_(\d+)_(\d+)\.py', p).groups())
        status, recs = parse(p)
        for kind, secs, fin, pid in recs:
            rows.append(dict(v=v, k=k, l=l, u=u, kind=kind, seconds=secs, finished=fin, pair=pid))
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    fig, ax = plt.subplots(figsize=(12, 7))
    # thin lines joining the CPU and wall time of the same run
    by_pair = {}
    for r in rows:
        if r['pair']:
            by_pair.setdefault((r['v'], r['k'], r['l'], r['u'], r['pair']), []).append(r)
    for rs in by_pair.values():
        ax.plot([r['k'] for r in rs], [r['seconds'] for r in rs], color='#bbbbbb', lw=1.2, zorder=1)
    style = {
        ('cpu', True): dict(marker='o', facecolors='#1f77b4', edgecolors='#0b3d63', label='CPU time, finished'),
        ('cpu', False): dict(marker='o', facecolors='none', edgecolors='#1f77b4', label='CPU time, stopped by a limit (at least)'),
        ('wall', True): dict(marker='s', facecolors='#ff7f0e', edgecolors='#8c4400', label='wall-clock time, finished'),
        ('wall', False): dict(marker='s', facecolors='none', edgecolors='#ff7f0e', label='wall-clock time, stopped by a limit (at least)'),
    }
    for (kind, fin), st in style.items():
        pts = [r for r in rows if r['kind'] == kind and r['finished'] == fin]
        if pts:
            ax.scatter([r['k'] for r in pts], [r['seconds'] for r in pts], s=52, linewidths=1.4, alpha=0.9, zorder=3, **st)
    ax.set_yscale('log')
    ax.set_xlabel('k (valency)')
    ax.set_ylabel('seconds, as recorded in the problem docstrings (log scale)')
    n = len({(r['v'], r['k'], r['l'], r['u']) for r in rows})
    ax.set_title(f'Run times recorded in problem_*.py docstrings: {len(rows)} timings for {n} parameter sets (grey line = same run, CPU vs wall)')
    ax.grid(True, which='both', alpha=0.25)
    # label the slowest runs, once per parameter set, alternating the offset so neighbouring labels do not overlap
    seen, i = set(), 0
    for r in sorted(rows, key=lambda r: -r['seconds']):
        q = (r['v'], r['k'], r['l'], r['u'])
        if q in seen or len(seen) >= 9:
            continue
        seen.add(q)
        ax.annotate(f"SRG{q}", (r['k'], r['seconds']), textcoords='offset points',
                    xytext=(7, (6, -13, 19)[i % 3]), fontsize=7.5, color='#333333')
        i += 1
    ax.legend(loc='upper left', frameon=True, fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f'saved {out}: {len(rows)} timings; cpu={sum(r["kind"] == "cpu" for r in rows)} wall={sum(r["kind"] == "wall" for r in rows)}')


if __name__ == '__main__':
    main()
