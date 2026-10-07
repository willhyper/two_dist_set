'''
Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.038s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.031s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 0.033s (1.06x)

solutions deduplicated by isomorphism: 2 labelings of 1 graph(s) -> 1 canonical matrix(es) (canon.canonical_matrix)
'''
v, k, l, u = 10, 6, 3, 4
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
