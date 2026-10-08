'''
STATUS: tackled - the search finished: these 1 graph(s) are ALL of them [the file now records 1 graph(s) in total, merged with its earlier results]
solutions deduplicated by isomorphism: 2 labelings of 1 graph(s) -> 1 canonical matrix(es) (canon.canonical_matrix)
'''
v, k, l, u = 15, 8, 4, 4
cpu_sec = 0.1744  # Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz, python3.14.7
wall_clock_sec = 0.229  # Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz, python3.14.7
solutions: list[str] = [
"""
011111111000000
101101100111000
110011100100110
110010011111000
101100011100110
111000110010101
111001001001011
100111001010101
100110110001011
011110000011110
010101010101101
010100101110011
001011010110011
001010101101101
000001111011110
""",
]
