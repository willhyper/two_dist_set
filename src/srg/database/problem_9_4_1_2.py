'''
Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz (4 cores), Darwin 15.7.3, python3.14.7
0.06091s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.014s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 0.014s (1.00x)
'''
v, k, l, u = 9, 4, 1, 2
solutions: list[str] = [
"""
011110000
101001100
110000011
100011010
100100101
010100110
010011001
001101001
001010110
""",
]
