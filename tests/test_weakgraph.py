__author__ = 'chaoweichen'

from two_dist_set.problem_database import problems
from two_dist_set import representation, weak_graph
from pprint import pprint

import pytest


@pytest.mark.parametrize('v,k,l,u,expected', problems)
def test_candidates(v, k, l, u, expected):
    adj_matrix = expected[0]
    scalars = representation.from_matrix(adj_matrix,v,k,l,u).to_scalars()

    pprint(adj_matrix)
    pprint(scalars)

    for slice in range(1, len(scalars)):
        current_state = scalars[:slice]
        ans = scalars[slice]

        possible_candidates = list(weak_graph._generate(current_state,v,k,l,u))
        assert ans in possible_candidates
        print(current_state, ans, possible_candidates)


def test_9_4_1_2():
    A = (240, 14, 56)

    Ans = (24, 20, 17, 12, 9, 6, 5)
    # [ [1, 1, 0, 0, 0],
    #   [1, 0, 1, 0, 0],
    #   [1, 0, 0, 0, 1],
    #   [0, 1, 1, 0, 0],
    #   [0, 1, 0, 0, 1],
    #   [0, 0, 1, 1, 0],
    #   [0, 0, 1, 0, 1],
    #  ]

    for c, a in zip(weak_graph._generate(A,9,4,1,2), Ans):
        assert c == a


def test_13_6_2_3():

    # Q_and_A = (4032, 1592, 294, 149, 77, 99, 26, 11, 14, 1, 3, 0)

    A = (4032,)
    weaks = list(weak_graph._generate(A,9,4,1,2))
    assert 1592 in weaks
