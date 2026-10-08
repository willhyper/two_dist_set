'''
STATUS: 1 of the 41 known graphs recorded (Paley(29)); the solver has NOT found any solution itself yet
Paley(29): vertices = Z/29, i ~ j iff i-j is a nonzero square mod 29. Written down directly from this construction,
NOT found by the search; verified with PartialSRG.solved() and stored in canonical form (canon.canonical_matrix).
Brouwer table srgtab1-50: exists (41 graphs) - complete enumeration by Bussemaker & Spence; Paley(29); 2-graph
Source: https://aeb.win.tue.nl/graphs/srg/srgtab1-50.html
Conference-type parameters (v = 4t+1, k = 2t, lambda = t-1, mu = t), so it is its own complement.
The other 40 graphs are not in this file; the runs below say what the solver itself has done so far.

Runs of the current solver (isomorph rejection + eigenvalue interlacing/Gram pruning, depth-first,
pure python, single process), Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7:
- first-solution search (max_solutions=1): no solution found after more than 30 minutes of CPU time
  (stopped by hand, the machine was shared with other searches), 2026-10-06
- full benchmark run (cap of 100 solutions): exceeded the 240s and 60s benchmark limits
For comparison, the same solver finds a first solution of SRG(27,10,1,5) in 3.9s, SRG(26,10,3,4) in
6.1s and SRG(25,12,5,6) in 13.8s, so this one is much harder than its neighbours.
'''
v, k, l, u = 29, 14, 6, 7
cpu_sec = None
wall_clock_sec = None
solutions: list[str] = [
"""
01111111111111100000000000000
10111111000000011111110000000
11010001110010010001011011001
11100010101100001100011001110
11000110100100111000101110001
11001001100011001110000111100
11011000011000110101000110110
11100100011001010010101101010
10111100000110000011001100111
10100011001010100110101010101
10010011010101001010010110011
10011000101001110010110001101
10100100110001101001110010110
10000101001110111101000001011
10001010010111000101111101000
01101011000101000001100011111
01011100001011000100111010011
01010110010001101011001001101
01000101111100000101110100101
01100010100011110110010100011
01001001010110111010011000110
01110000001110101011100111000
00111001110000101100100101011
00001111101000100011011011010
00101110011010011000010101101
00110101000101110100011110100
00010110110110010110100011010
00010011101011011001101100100
00101000111101011111001010000
""",
]
