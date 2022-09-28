
from srg.srg import SRG
from srg import database as db
from srg import util
from srg import strong_graph
import numpy as np
import pytest


def collect_problems():
    problems_all = []
    problems = db.list_problems()
    for p in problems:
        v,k,l,u = db.extract_vklu(p)
        solutions = db.get_solutions(v,k,l,u)
        problems_all.append((v,k,l,u, solutions))
    return problems_all
problems = collect_problems()


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
    s = util.generate_seed(v, k, l, u)
    g = strong_graph.advance(s)

    try:
        ss = g.__iter__().__next__()
    except StopIteration:
        pass
    else:
        last_state = s.copy()
        expected_state = ss.copy()
        d = expected_state - last_state
        actual = last_state + d

        assert actual == expected_state
        assert actual != last_state
