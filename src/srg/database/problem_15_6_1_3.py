'''
STATUS: tackled - solved by the solver (its fastest finished run is in cpu_sec / wall_clock_sec below)
solutions deduplicated by isomorphism: 2 labelings of 1 graph(s) -> 1 canonical matrix(es) (canon.canonical_matrix)
'''
v, k, l, u = 15, 6, 1, 3
cpu_sec = 0.07  # Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz, python3.14.7
wall_clock_sec = 0.056  # Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz, python3.14.7
solutions: list[str] = [
"""
011111100000000
101000011110000
110000000001111
100010011001100
100100000110011
100000111000011
100001000111100
010101000101010
010101000010101
010010110000101
010010101001010
001100110010001
001100101100010
001011010010100
001011001101000
""",
]
