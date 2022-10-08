__author__ = 'chaoweichen'

from srg import utils
from srg import database as db
from srg import srg
from srg import sorter
import numpy as np

import pytest

problems_all = []

problems = db.list_problems()
for p in problems:
    v,k,l,u = db.extract_vklu(p)
    solutions = db.get_solutions(v,k,l,u)
    problems_all.append((v,k,l,u, solutions))


@pytest.mark.parametrize('v,k,l,u, database', problems_all)
def test_matrix_property(v: int, k: int, l: int, u: int, database):
    '''

    in any given partial adj matrix, a property holds.

    For example, the first 3 row of question (9, 4, 1, 2) is known,
    and the 4th row is under construction.
    Once ?????, the 1x5 vector, is found. It must follow some requirements from the first 3 rows.

    011110000
    101001100
    110000011
    1000????? <= ????? = solution

    test below is given the complete SRG matrix. Therefore, the solution is known.
    We use the solution to test against the property

    '''
    for mat in database:
        for ri in range(1, v - 1):
            mr = mat[:ri, :]
            m_left, pivot, m_right = mr[:, :ri], mr[:, ri], mr[:, ri+1:] 
            lu = [l if e else u for e in pivot]
            solution = mat[ri, ri + 1:]
            assert np.array_equal(m_left @ pivot + m_right @ solution, lu)


@pytest.mark.parametrize('v,k,l,u, database', problems_all)
def test_determinant(v: int, k: int, l: int, u: int, database):
    '''
    determinant can be obtained by two ways, so we want them agree with each other

    det_from_matrix, calculated from matrix, from database
    det_expected, derived from SRG requirements: eigenvalues and their multiplicity are already known
    '''
    not_conference_graph = utils.conference(v, k, l, u) != 0

    det_expected = utils.determinant(v, k, l, u)
    for mat in database:
        eigval, eigvec = np.linalg.eig(mat)

        eigval = tuple(int(np.round(x)) for x in eigval) if not_conference_graph else eigval

        det_from_matrix = np.prod(eigval)
        det_from_matrix = int(np.round(det_from_matrix))
        assert det_from_matrix == det_expected, "determinant disagree"


@pytest.mark.parametrize('v,k,l,u, database', problems_all)
def test_srg_matrix_identity(v: int, k: int, l: int, u: int, database):
    I = srg.identity(v)
    J = srg.ones((v, v))
    const = (k - u) * I + u * J
    for mat in database:
        assert np.array_equal(mat @ mat - (l - u) * mat, const)

    cmat = map(utils.complement, database)
    #cmat = map(sorter.maximize, cmat) # does not matter do maximize or not
    cv, ck, cl, cu = utils.complement_vklu(v,k,l,u)
    cconst = (ck - cu) * I + cu * J
    for mat in cmat:
        assert np.array_equal(mat @ mat - (cl - cu) * mat, cconst)