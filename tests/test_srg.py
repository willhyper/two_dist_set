
from two_dist_set.srg import SRG
from two_dist_set.problem_database import *
import two_dist_set
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
    for mat_expected in expected:
        s = SRG.from_matrix(mat_expected, v, k, l, u)

        mat_actual = s.to_matrix()
        assert np.array_equal(mat_expected, mat_actual)

        mat_partial_actual = s.to_matrix_essential()
        mat_partial_expected = mat_expected[:s.state, :]
        assert np.array_equal(mat_partial_expected, mat_partial_actual)


@pytest.mark.parametrize('v,k,l,u, expected', problems)
def test_add_sub_eq(v, k, l, u, expected):
    s = two_dist_set.util.generate_seed(v, k, l, u)
    g = two_dist_set.strong_graph.advance(s)
    ss = next(g)

    last_state = s.copy()
    expected_state = ss.copy()
    d = expected_state - last_state
    actual = last_state + d

    assert actual == expected_state
    assert actual != last_state

