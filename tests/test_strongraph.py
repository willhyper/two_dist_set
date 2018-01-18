__author__ = 'chaoweichen'

import two_dist_set

from two_dist_set import util, strong_graph
from two_dist_set.problem_database import *


import numpy as np
from collections import deque

import pytest

problems_efficient = []
problems_efficient.append(problem_4_2_0_2)
problems_efficient.append(problem_5_2_0_1)
problems_efficient.append(problem_6_3_0_3)
problems_efficient.append(problem_6_4_2_4)
problems_efficient.append(problem_9_4_1_2)
problems_efficient.append(problem_10_3_0_1)
problems_efficient.append(problem_10_6_3_4)
problems_efficient.append(problem_12_6_0_6)
problems_efficient.append(problem_13_6_2_3)
problems_efficient.append(problem_15_8_4_4) # 0.12s partition
problems_efficient.append(problem_16_5_0_2)
problems_efficient.append(problem_16_6_2_2)
problems_efficient.append(problem_16_9_4_6) # 0.17s partition
problems_efficient.append(problem_16_10_6_6) # 0.66s partition
problems_efficient.append(problem_17_8_3_4) # 0.41s partition

problems_all = problems_efficient.copy()
# problems_all.append(problem_21_10_4_5)  # no solution. 164s weak. 276.53s partition.
# problems_all.append(problem_21_10_5_4)  # 42.94s weak. 46s partition.
problems_all.append(problem_25_8_3_2)  # 2.43s weak. 0.25s partition.
# problems_all.append(problem_25_12_5_6)  # Total 15! solutions. too many. only list the first
# problems_all.append(problem_26_10_3_4)  # Total 10! solutions. too many. only list the first
# problems_all.append(problem_27_10_1_5)  # 256.58s weak. 82.78s partition. after cythonized, 262.96s weak, ??s partition.


@pytest.mark.parametrize('v,k,l,u,database', problems_all)
def test_weak_algo_output_agree_w_database(v: int, k: int, l: int, u: int, database):
    seed = util.generate_seed(v, k, l, u)

    actual_srgs = list(strong_graph.solve(seed, approach=strong_graph._advance_from_weak))
    assert len(actual_srgs) == len(database)

    actual_srgs.sort()

    for actual_srg, expected_matrix in zip(actual_srgs, database):
        actual_matrix = actual_srg.to_matrix()
        assert np.array_equal(actual_matrix, expected_matrix)


@pytest.mark.parametrize('v,k,l,u,database', problems_all)
def test_partition_algo_output_agree_w_database(v: int, k: int, l: int, u: int, database):
    seed = util.generate_seed(v, k, l, u)

    actual_srgs = list(strong_graph.solve(seed, approach=strong_graph._advance_from_partition))
    assert len(actual_srgs) == len(database)

    actual_srgs.sort()

    for actual_srg, expected_matrix in zip(actual_srgs, database):
        actual_matrix = actual_srg.to_matrix()
        assert np.array_equal(actual_matrix, expected_matrix)


@pytest.mark.parametrize('v,k,l,u,database', problems_efficient)
def test_compare_two_approaches(v: int, k: int, l: int, u: int, database):
    '''
    _advance_from_weak is an early approach
    _advance_from_partition is the current approach
    both should output the same, even in their intermediate state
    '''
    s = two_dist_set.util.generate_seed(v, k, l, u)

    q = deque()
    q.append(s)

    while q:

        s = q.pop()

        wk = list(two_dist_set.strong_graph._advance_from_weak(s))
        pt = list(two_dist_set.strong_graph._advance_from_partition(s))
        wk.sort()
        pt.sort()

        for w, p in zip(wk, pt):
            assert w == p

        for ss in pt:
            q.append(ss)
