
from two_dist_set.srg import SRG
from two_dist_set.problem_database import *

import numpy as np
import pytest

problems = []
problems.append(problem_4_2_0_2)
problems.append(problem_5_2_0_1)
problems.append(problem_6_3_0_3)
problems.append(problem_6_4_2_4)
problems.append(problem_9_4_1_2)
problems.append(problem_10_3_0_1)
problems.append(problem_10_6_3_4)
problems.append(problem_12_6_0_6)
problems.append(problem_13_6_2_3)
problems.append(problem_15_8_4_4)
problems.append(problem_16_5_0_2)
problems.append(problem_16_6_2_2)
problems.append(problem_16_9_4_6)
problems.append(problem_16_10_6_6)
problems.append(problem_17_8_3_4)

@pytest.mark.parametrize('v,k,l,u, expected', problems)
def test_data_structure(v, k, l, u, expected):
    for expected_one in expected:
        s = SRG.from_matrix(expected_one, v, k, l, u)
        actual = s.to_matrix()
        assert np.array_equal(expected_one, actual)
