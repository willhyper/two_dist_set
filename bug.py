from two_dist_set import database, sort
import numpy as np


J = np.ones((10, 10), dtype=np.uint8)
I = np.eye(10, dtype=np.uint8)

v, k, l, u = 10, 6, 3, 4
problem = database.problem_10_6_3_4


a1, a2 = problem[4]

def check(m, v=10, k=6, l=3, u=4):
    r1 = m @ m
    r2 = k*I + l*m + u*(J-I-m)
    print(r1)
    print(r2)
    print('equal ? ', np.array_equal(r1,r2))

def comp(m, _sort = True):
    mc = 1 - m
    for i in range(v): mc[i,i]=0


    if _sort:
        return sort(mc)
    else:
        return mc


b1, b2 = comp(a1), comp(a2)

d = b1 - b2

