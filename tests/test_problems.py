from two_dist_set.srg import SRG

__author__ = 'chaoweichen'

from two_dist_set import strong_graph
from two_dist_set.problem_database import *

import numpy as np

import pytest

problems = []
problems.append(problem_17_8_3_4)
problems.append(problem_15_8_4_4)
problems.append(problem_13_6_2_3)
#problems.append(problem_21_10_5_4)
@pytest.mark.parametrize('v,k,l,u,expected', problems)
def test_srg(v, k, l, u, expected):
    seed = strong_graph.generate_seed(v, k, l, u)

    s = SRG(v,k,l,u)
    s.add(seed)

    actual = list(strong_graph.generate(s))
    assert len(actual) == len(expected)

    for g, e in zip(actual, expected):
        assert np.array_equal(g, e)
