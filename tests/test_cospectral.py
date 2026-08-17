__author__ = 'Chao-Wei Chen, madmath0902@gmail.com'

from srg.srg import PartialSRG
from srg.database.problem_10_6_3_4 import v, k, l, u, solutions
import numpy as np

A, B = solutions
A = PartialSRG(solutions[0])
B = PartialSRG(solutions[1])
Ac = A.complement_matrix(maximize=True)
Bc = B.complement_matrix(maximize=True)
assert np.array_equal(Ac._matrix, Bc._matrix)
assert Ac.solved()
assert Bc.solved()


# def test_cospectral():
#     print("Testing cospectrality...")


Acc = Ac.complement_matrix(maximize=True)
assert Acc.solved()

print(A)
print(B)
print(Acc)

