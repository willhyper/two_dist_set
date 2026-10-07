__author__ = 'Chao-Wei Chen, madmath0902@gmail.com'

import numpy as np
import pytest

from srg import database as db
from srg.model import PartialSRG


@pytest.mark.xfail(reason='sorter.maximize is not a canonical form: two relabelings of the same graph '
                          'can maximize to different matrices (use canon.canonical_matrix instead)')
def test_complements_of_two_labelings_maximize_to_the_same_matrix():
    A = PartialSRG(db.get_solutions(10, 6, 3, 4)[0])
    perm = np.random.default_rng(0).permutation(10)
    B = PartialSRG(A._matrix[perm][:, perm])  # the same graph, relabeled

    Ac = A.complement_matrix(maximize=True)
    Bc = B.complement_matrix(maximize=True)
    assert Ac.solved() and Bc.solved()
    assert np.array_equal(Ac._matrix, Bc._matrix)

    Acc = Ac.complement_matrix(maximize=True)
    assert Acc.solved()
