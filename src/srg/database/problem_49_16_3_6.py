'''
STATUS: tackled - UNDECIDED: no solution found within the 21600s time limit
Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz (4 cores), Darwin 15.7.3, python3.14.7
search stopped without finishing; not a proof of non-existence. It received only ~9,040s (~150 min) of CPU: the 6h limit was
measured in wall-clock (41209s here) and most of that time the process was paused to free the CPU for other jobs
Brouwer table srgtab1-50: does not exist (does not exist) - Bussemaker-Haemers-Mathon-Wilbrink
Source: https://aeb.win.tue.nl/graphs/srg/srgtab1-50.html
Complement: problem_49_32_21_20 (derive from this one when done)
'''

status = 'undecided'  # placeholder: not tackled yet, the empty solutions list below is NOT a proof of anything

v, k, l, u = 49, 16, 3, 6
solutions: list = []
