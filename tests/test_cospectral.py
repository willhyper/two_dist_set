__author__ = 'Chao-Wei Chen, madmath0902@gmail.com'

from srg.model import PartialSRG
from srg import database as db
import numpy as np

solutions = db.get_solutions(10, 6, 3, 4)
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

