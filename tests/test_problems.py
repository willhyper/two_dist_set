__author__ = 'chaoweichen'

from two_dist_set import strong_graph
from two_dist_set.problem_database import problems

import numpy as np

import pytest


@pytest.mark.parametrize('v,k,l,u,expected', problems)
def test_srg(v, k, l, u, expected):
    seed = strong_graph.generate_seed(v, k, l, u)

    actual = list(strong_graph.generate(seed, v, k, l, u))
    assert len(actual) == len(expected)

    for g, e in zip(actual, expected):
        assert np.array_equal(g, e)
