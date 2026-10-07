'''
STATUS: tackled - UNDECIDED so far: the solver has not yet found any solution
This SRG DOES exist, so the empty `solutions` list below is NOT a proof of anything.
Brouwer table srgtab1-50: exists (41 graphs) - complete enumeration by Bussemaker & Spence; Paley(29); 2-graph
Source: https://aeb.win.tue.nl/graphs/srg/srgtab1-50.html
Conference-type parameters (v = 4t+1, k = 2t, lambda = t-1, mu = t), so it is its own complement.

Runs of the current solver (isomorph rejection + eigenvalue interlacing/Gram pruning, depth-first,
pure python, single process), Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7:
- first-solution search (max_solutions=1): no solution found after more than 30 minutes of CPU time
  (stopped by hand, the machine was shared with other searches), 2026-10-06
- full benchmark run (cap of 100 solutions): exceeded the 240s and 60s benchmark limits
For comparison, the same solver finds a first solution of SRG(27,10,1,5) in 3.9s, SRG(26,10,3,4) in
6.1s and SRG(25,12,5,6) in 13.8s, so this one is much harder than its neighbours.
'''
status = 'todo'  # placeholder: not solved yet (see STATUS above)

v, k, l, u = 29, 14, 6, 7
solutions: list[str] = []
