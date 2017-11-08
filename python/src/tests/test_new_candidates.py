__author__ = 'chaoweichen'

from two_dist_set.problem_database import problems
from two_dist_set import representation, candidates, globalz
from pprint import pprint

import pytest


@pytest.mark.parametrize('v,k,l,u,expected', problems)
def test_candidates(v,k,l,u, expected):

    globalz.set_problem(v,k,l,u)
    adj_matrix = expected[0]
    scalars = representation.from_matrix(adj_matrix).to_scalars()

    pprint(adj_matrix)
    pprint(scalars)

    for slice in range(1, len(scalars)):
        current_state = scalars[:slice]
        ans = scalars[slice]

        possible_candidates = list(candidates.generate(current_state))
        assert ans in possible_candidates
        print(current_state, ans, possible_candidates)
