'''
Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.038s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.031s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 0.033s (1.06x)
'''
v, k, l, u = 10, 6, 3, 4
solutions: list[str] = [
"""
0111111000
1011100110
1100011110
1100110101
1101001011
1011001101
1010110011
0111010011
0110101101
0001111110
""",
"""
0111111000
1011100110
1101010101
1110001011
1100011110
1010101101
1001110011
0110110011
0101101101
0011011110
""",
]
