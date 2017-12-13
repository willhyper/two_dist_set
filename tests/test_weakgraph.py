from two_dist_set.srg import SRG

__author__ = 'chaoweichen'

import numpy as np
from two_dist_set.problem_database import *
from two_dist_set import weak_graph
from pprint import pprint

import pytest

problems = [problem_15_8_4_4, problem_21_10_5_4]


@pytest.mark.parametrize('v,k,l,u,expected', problems)
def test_candidates(v, k, l, u, expected):
    if len(expected) == 0:  # no solution. no bother check
        return

    adj_matrix = expected[0]
    s = SRG(v, k, l, u)
    i = s.state
    while i < v - 1:
        row = adj_matrix[i, i + 1:]
        s.add(row)

        ans = adj_matrix[i + 1, i + 2:]
        weaks = list(weak_graph.generate(s))
        for w in weaks:
            if np.array_equal(ans, w):
                break
        else:
            assert False, "design error"

        i += 1
