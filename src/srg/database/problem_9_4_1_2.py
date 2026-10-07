'''
Intel(R) Core(TM) i5-4258U CPU @ 2.40GHz (4 cores), Darwin 15.7.3, python3.14.7
0.06091s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process
'''
from srg.model import array

v, k, l, u = 9, 4, 1, 2
solutions: list = [array([[0, 1, 1, 1, 1, 0, 0, 0, 0],
                          [1, 0, 1, 0, 0, 1, 1, 0, 0],
                          [1, 1, 0, 0, 0, 0, 0, 1, 1],
                          [1, 0, 0, 0, 1, 1, 0, 1, 0],
                          [1, 0, 0, 1, 0, 0, 1, 0, 1],
                          [0, 1, 0, 1, 0, 0, 1, 1, 0],
                          [0, 1, 0, 0, 1, 1, 0, 0, 1],
                          [0, 0, 1, 1, 0, 1, 0, 0, 1],
                          [0, 0, 1, 0, 1, 0, 1, 1, 0]])]
