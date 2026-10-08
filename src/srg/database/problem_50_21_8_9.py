'''
STATUS: tackled - UNDECIDED: no solution found within the 10800s time limit
search stopped after 10809s without finishing; not a proof of non-existence
Brouwer table srgtab1-50: exists (many graphs) - switch OA(7,4)+*; switch skewhad2+*; 2-graph
Source: https://aeb.win.tue.nl/graphs/srg/srgtab1-50.html
Complement: problem_50_28_15_16 (derive from this one when done)
'''

status = 'undecided'  # placeholder: not tackled yet, the empty solutions list below is NOT a proof of anything

v, k, l, u = 50, 21, 8, 9
cpu_sec = None
wall_clock_sec = None
solutions: list = []
