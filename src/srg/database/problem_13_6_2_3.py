'''
Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.067s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.052s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 0.065s (1.25x)

solutions deduplicated by isomorphism: 2 labelings of 1 graph(s) -> 1 canonical matrix(es) (canon.canonical_matrix)
'''
v, k, l, u = 13, 6, 2, 3
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
