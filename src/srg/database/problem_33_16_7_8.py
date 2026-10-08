'''
STATUS: tackled - UNDECIDED: no solution found within the 21600s time limit
search stopped without finishing; not a proof of non-existence. It received only ~9,040s (~150 min) of CPU: the 6h limit was
measured in wall-clock (41,207s here) and most of that time the process was paused to free the CPU for other jobs
Brouwer table srgtab1-50: does not exist (does not exist) - Conf
Source: https://aeb.win.tue.nl/graphs/srg/srgtab1-50.html
'''

status = 'undecided'  # placeholder: not tackled yet, the empty solutions list below is NOT a proof of anything

v, k, l, u = 33, 16, 7, 8
cpu_sec = None
wall_clock_sec = None
solutions: list = []
