'''
STATUS: tackled - UNDECIDED: no solution found within the 21600s time limit
search stopped after 21604s without finishing; not a proof of non-existence
Brouwer table srgtab1-50: exists (180 graphs) - U3(3).2 / L2(7).2 - subconstituent of Hall-Janko graph; complete enumeration by McKay & Spence; RSHCD–; 2-graph
Source: https://aeb.win.tue.nl/graphs/srg/srgtab1-50.html
Complement: problem_36_21_12_12 (derive from this one when done)
'''

status = 'undecided'  # placeholder: not tackled yet, the empty solutions list below is NOT a proof of anything

v, k, l, u = 36, 14, 4, 6
cpu_sec = None
wall_clock_sec = None
solutions: list = []
