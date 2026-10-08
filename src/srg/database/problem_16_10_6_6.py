'''
STATUS: tackled - the search finished: these 1 graph(s) are ALL of them [the file now records 1 graph(s) in total, merged with its earlier results]
solutions deduplicated by isomorphism: 2 labelings of 1 graph(s) -> 1 canonical matrix(es) (canon.canonical_matrix)
'''
v, k, l, u = 16, 10, 6, 6
cpu_sec = 0.3839  # Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz, python3.14.7
wall_clock_sec = 0.5538  # Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz, python3.14.7
solutions: list[str] = [
"""
0111111111100000
1011110110011100
1101101101011010
1110011100110110
1110011011011001
1101101010110101
1011110001110011
1111000011101110
1100110101101101
1010101110101011
1001011111000111
0111111000001111
0110100111010111
0101010110111011
0011001101111101
0000111011111110
""",
]
