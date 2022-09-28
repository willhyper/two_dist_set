__author__ = 'chaoweichen'

from srg.srg import SRG
from srg import weak_graph
from srg import database as db

import numpy as np
import pytest


def collect_problems():
    p1 = (15,8,4,4,db.get_solutions(15,8,4,4))
    p2 = (21,10,5,4,db.get_solutions(21,10,5,4))
    return [p1,p2]
problems = collect_problems()

@pytest.mark.parametrize('v,k,l,u,expected', problems)
def test_candidates(v, k, l, u, expected):
    if len(expected) == 0:  # no solution. no bother check
        return

    adj_matrix = expected[0]
    s = SRG(v, k, l, u)
    i = s.state
    while i < v - 1:
        row = adj_matrix[i, i + 1:]
        s += row

        ans = adj_matrix[i + 1, i + 2:]
        weaks = list(weak_graph.advance(s))
        for w in weaks:
            if np.array_equal(ans, w):
                break
        else:
            assert False, "design error"

        i += 1
