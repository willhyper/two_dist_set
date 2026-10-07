'''
no solution.
Apple M1. python3.10
71.05s. cythonized
23s. multi-threaded
20.77. multi-threaded, cythonized

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
579.39s. pure python, single process, no cython
43.134s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
26.325s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 25.384s (0.96x)
'''
from srg.model import array

v, k, l, u = 21, 10, 4, 5
solutions: list = []
