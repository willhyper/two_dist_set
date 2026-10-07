'''
Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.054s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.045s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 0.07s (1.56x)
'''
v, k, l, u = 12, 6, 0, 6
solutions: list[str] = [
"""
011111100000
100000011111
100000011111
100000011111
100000011111
100000011111
100000011111
011111100000
011111100000
011111100000
011111100000
011111100000
""",
]
