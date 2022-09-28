#!python
#cython: language_level=3

def conference(v: int, k: int, l: int, u: int):
    return 2 * k + (v - 1) * (l - u)
