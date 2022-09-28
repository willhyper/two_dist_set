
from srg.srg import SRG
from srg import database as db
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

