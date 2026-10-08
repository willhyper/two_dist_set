'''
STATUS: tackled - UNDECIDED: no solution found within the 10800s time limit
search stopped after 10872s without finishing; not a proof of non-existence
Brouwer table srgtab1-50: exists (many graphs) - Mathon; 2-graph*
Source: https://aeb.win.tue.nl/graphs/srg/srgtab1-50.html
'''

status = 'undecided'  # placeholder: not tackled yet, the empty solutions list below is NOT a proof of anything

v, k, l, u = 45, 22, 10, 11
cpu_sec = None
wall_clock_sec = None
solutions: list = []
