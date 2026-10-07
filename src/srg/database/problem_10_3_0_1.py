'''
Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.024s. isomorph rejection + eigenvalue interlacing pruning, pure python, single process

Intel Core i5-4258U 2.40GHz (4 cores), macOS 15.7.3, python3.14.7
0.016s. cythonized (./cythonize.sh: all modules, Cython 3.3, annotation_typing=False); same session pure python: 0.025s (1.56x)
'''
v, k, l, u = 10, 3, 0, 1
solutions: list[str] = [
"""
0111000000
1000110000
1000001100
1000000011
0100001010
0100000101
0010100001
0010010010
0001100100
0001011000
""",
]
