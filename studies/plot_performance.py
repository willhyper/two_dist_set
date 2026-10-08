'''
Scatter plot of the fastest finished solver run recorded in each problem file: x = k (linear), y = seconds (log).

Every problem_*.py stores two variables, cpu_sec and wall_clock_sec: the fastest finished run of the solver on that
quest (None if it was never finished). The builder only ever replaces them with a faster run. CPU time and wall-clock
time are plotted as separate series; a grey line joins the two numbers of one quest (their gap is the time the process
spent waiting for a busy or shared CPU).

Run:  python studies/plot_performance.py out.png [out.csv]
'''
import csv
import importlib
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from srg import database as db


def main():
    rows = []
    for name in sorted(db.list_problems()):
        m = importlib.import_module('srg.database.' + name)
        if m.cpu_sec is not None or m.wall_clock_sec is not None:
            rows.append(dict(v=m.v, k=m.k, l=m.l, u=m.u, cpu_sec=m.cpu_sec, wall_clock_sec=m.wall_clock_sec))
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    fig, ax = plt.subplots(figsize=(11, 6.5))
    for r in rows:
        if r['cpu_sec'] is not None and r['wall_clock_sec'] is not None:
            ax.plot([r['k'], r['k']], [r['cpu_sec'], r['wall_clock_sec']], color='#bbbbbb', lw=1.2, zorder=1)
    cpu = [r for r in rows if r['cpu_sec'] is not None]
    wall = [r for r in rows if r['wall_clock_sec'] is not None]
    ax.scatter([r['k'] for r in cpu], [r['cpu_sec'] for r in cpu], s=55, marker='o', facecolors='#1f77b4',
               edgecolors='#0b3d63', linewidths=1.3, zorder=3, label='cpu_sec (CPU time)')
    ax.scatter([r['k'] for r in wall], [r['wall_clock_sec'] for r in wall], s=55, marker='s', facecolors='#ff7f0e',
               edgecolors='#8c4400', linewidths=1.3, zorder=3, label='wall_clock_sec (wall-clock time)')
    ax.set_yscale('log')
    ax.set_xlabel('k (valency)')
    ax.set_ylabel('seconds, fastest finished run (log scale)')
    ax.set_title(f'SRG(v,k,λ,μ): fastest finished solver run recorded in the problem files ({len(rows)} quests)')
    ax.grid(True, which='both', alpha=0.25)
    slowest = sorted(rows, key=lambda r: -(r['wall_clock_sec'] or r['cpu_sec']))[:7]
    for i, r in enumerate(slowest):
        ax.annotate(f"SRG({r['v']},{r['k']},{r['l']},{r['u']})", (r['k'], r['wall_clock_sec'] or r['cpu_sec']),
                    textcoords='offset points', xytext=(7, (6, -13, 19)[i % 3]), fontsize=7.5, color='#333333')
    ax.legend(loc='upper left', frameon=True)
    fig.tight_layout()
    fig.savefig(sys.argv[1], dpi=150)
    print(f'saved {sys.argv[1]}: {len(rows)} quests with a recorded finished run')


if __name__ == '__main__':
    main()
