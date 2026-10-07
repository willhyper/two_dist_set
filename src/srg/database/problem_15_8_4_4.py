'''
Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.229s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.166s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 0.19s (1.14x)

solutions deduplicated by isomorphism: 2 labelings of 1 graph(s) -> 1 canonical matrix(es) (canon.canonical_matrix)
'''
v, k, l, u = 15, 8, 4, 4
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
