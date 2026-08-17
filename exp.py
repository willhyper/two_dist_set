'''
investigate how 10_6_3_4 degenerate to 10_3_0_1
'''
from srg import sorter
from srg.srg import PartialSRG
import numpy as np
from srg.database import problem_10_6_3_4 as pp
from srg.database import problem_10_3_0_1 as pn

s0, s1 = pp.solutions

t0 = PartialSRG(s0).complement_matrix()._matrix
t1 = PartialSRG(s1).complement_matrix()._matrix

u0 = sorter.maximize(t0)
u1 = sorter.maximize(t1)

v = pn.solutions[0]

np.array_equal(u0, v)
np.array_equal(u1, v)

