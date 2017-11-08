__author__ = 'chaoweichen'

from two_dist_set import globalz, strong_graph
from two_dist_set.problem_database import problems

import numpy as np

import pytest


@pytest.mark.parametrize('v,k,l,u,expected', problems)
def test_srg(v, k, l, u, expected):
    globalz.set_problem(v, k, l, u)
    seed = globalz.generate_seed()

    for g, e in zip(strong_graph.generate(seed), expected):
        assert np.array_equal(g, e)
