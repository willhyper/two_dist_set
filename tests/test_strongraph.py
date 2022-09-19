__author__ = 'chaoweichen'


from two_dist_set import util
from two_dist_set import strong_graph
from two_dist_set import database as db


import numpy as np
import pytest

def collect_problems():
    out = []
    problems = db.list_problems()
    for p in problems:
        v,k,l,u = db.extract_vklu(p)
        if v > 18: continue
        solutions = db.get_solutions(v,k,l,u)
        out.append((v,k,l,u,solutions))
    return out
problems = collect_problems()


@pytest.mark.parametrize('v,k,l,u,database', problems)
def test_partition_algo_output_agree_w_database(v: int, k: int, l: int, u: int, database):
    seed = util.generate_seed(v, k, l, u)

    actual_srgs = list(strong_graph.solve(seed))
    assert len(actual_srgs) == len(database)

    actual_srgs.sort()

    for actual_srg, expected_matrix in zip(actual_srgs, database):
        actual_matrix = actual_srg.to_matrix()
        assert np.array_equal(actual_matrix, expected_matrix)


