'''
STATUS: tackled - solved by the solver (its fastest finished run is in cpu_sec / wall_clock_sec below)
solutions deduplicated by isomorphism: 2 labelings of 1 graph(s) -> 1 canonical matrix(es) (canon.canonical_matrix)
'''
v, k, l, u = 10, 6, 3, 4
cpu_sec = 0.033  # Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz, python3.14.7
wall_clock_sec = 0.038  # Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz, python3.14.7
solutions: list[str] = [
"""
0111111000
1011010110
1100110101
1100101110
1011001101
1110001011
1001110011
0111100011
0101011101
0010111110
""",
]
