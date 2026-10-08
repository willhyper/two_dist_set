'''
STATUS: tackled - solved by the solver (its fastest finished run is in cpu_sec / wall_clock_sec below)
solutions deduplicated by isomorphism: 2 labelings of 1 graph(s) -> 1 canonical matrix(es) (canon.canonical_matrix)
'''
v, k, l, u = 13, 6, 2, 3
cpu_sec = 0.065  # Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz, python3.14.7
wall_clock_sec = 0.067  # Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz, python3.14.7
solutions: list[str] = [
"""
0111111000000
1011000111000
1100100010110
1100010100101
1010001100011
1001001001110
1000110011001
0101100001011
0110001001101
0100011110010
0011010010011
0010110101100
0001101110100
""",
]
