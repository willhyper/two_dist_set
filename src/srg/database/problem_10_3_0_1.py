'''
Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.024s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process
'''
from srg.model import array

v, k, l, u = 10, 3, 0, 1
solutions: list = [array([[0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                          [1, 0, 0, 0, 1, 1, 0, 0, 0, 0],
                          [1, 0, 0, 0, 0, 0, 1, 1, 0, 0],
                          [1, 0, 0, 0, 0, 0, 0, 0, 1, 1],
                          [0, 1, 0, 0, 0, 0, 1, 0, 1, 0],
                          [0, 1, 0, 0, 0, 0, 0, 1, 0, 1],
                          [0, 0, 1, 0, 1, 0, 0, 0, 0, 1],
                          [0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
                          [0, 0, 0, 1, 1, 0, 0, 1, 0, 0],
                          [0, 0, 0, 1, 0, 1, 1, 0, 0, 0]])]
