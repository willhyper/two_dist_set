'''
Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.056s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.05s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 0.07s (1.40x)

solutions deduplicated by isomorphism: 2 labelings of 1 graph(s) -> 1 canonical matrix(es) (canon.canonical_matrix)
'''
v, k, l, u = 15, 6, 1, 3
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
