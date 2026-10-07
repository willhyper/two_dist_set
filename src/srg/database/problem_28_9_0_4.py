'''
no solution.
Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz (4 cores), Darwin 15.7.3, python3.14.7
128.3s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
31.179s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 29.568s (0.95x)
'''
from srg.model import array

v, k, l, u = 28, 9, 0, 4
solutions: list = []
