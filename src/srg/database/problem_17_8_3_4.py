'''
Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.434s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.29s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 0.336s (1.16x)

solutions deduplicated by isomorphism: 6 labelings of 1 graph(s) -> 1 canonical matrix(es) (canon.canonical_matrix)
'''
v, k, l, u = 17, 8, 3, 4
solutions: list[str] = [
"""
01111111100000000
10111000011110000
11000110001101001
11000011011000110
11000100110011100
10101001010001011
10110000100101110
10010100101010011
10001011000110101
01011100000100111
01110001000011101
01100010110010011
01001001101101010
00101110001010110
00011010111001001
00010111010111000
00100101111100100
""",
]
