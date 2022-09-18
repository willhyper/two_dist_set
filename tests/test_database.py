__author__ = 'chaoweichen'

import two_dist_set

from two_dist_set import strong_graph, conference, util
from two_dist_set.database import *
from two_dist_set import srg

import numpy as np

import pytest

problems_all = []
problems_all.append(problem_4_2_0_2)
problems_all.append(problem_5_2_0_1)
problems_all.append(problem_6_3_0_3)
problems_all.append(problem_6_4_2_4)
problems_all.append(problem_9_4_1_2)
problems_all.append(problem_10_3_0_1)
problems_all.append(problem_10_6_3_4)
problems_all.append(problem_12_6_0_6)
problems_all.append(problem_13_6_2_3)
problems_all.append(problem_15_8_4_4)
problems_all.append(problem_16_5_0_2)
problems_all.append(problem_16_6_2_2)
problems_all.append(problem_16_9_4_6)
problems_all.append(problem_16_10_6_6)
problems_all.append(problem_17_8_3_4)
problems_all.append(problem_21_10_4_5)  # no solution.
problems_all.append(problem_21_10_5_4)
problems_all.append(problem_25_8_3_2)
problems_all.append(problem_25_12_5_6)  # Total 15! solutions. too many. only list the first
problems_all.append(problem_26_10_3_4)  # Total 10! solutions. too many. only list the first
problems_all.append(problem_27_10_1_5)


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

            partial_mat = mat[:ri, :]
            s = srg.SRG.from_matrix(partial_mat, v, k, l, u)

            m_right, inner_prod_remain = s.question()

            # part 1: solution is known: mat[ri, ri + 1:]
            solution = mat[ri, ri + 1:]
            assert np.array_equal(m_right @ solution, inner_prod_remain)

            # part 2: solution is not known: generate candidates from strong_generator
            for s2 in strong_graph.advance(s):
                candidate = s2 - s
                assert np.array_equal(m_right @ candidate, inner_prod_remain)


@pytest.mark.parametrize('v,k,l,u, database', problems_all)
def test_matrix_is_sorted(v: int, k: int, l: int, u: int, database):
    '''
    because SRG class defines how to compare its data structure so we can 'sort' matrix
    see how SRG can be decorated with @total_ordering
    '''
    actual = database
    srg_actual = [two_dist_set.srg.SRG.from_matrix(mat, v, k, l, u) for mat in actual]

    srg_expected = sorted(srg_actual)

    for a, e in zip(srg_actual, srg_expected):
        assert a == e


@pytest.mark.parametrize('v,k,l,u, database', problems_all)
def test_determinant(v: int, k: int, l: int, u: int, database):
    '''
    determinant can be obtained by two ways, so we want them agree with each other

    det_from_matrix, calculated from matrix, from database
    det_expected, derived from SRG requirements: eigenvalues and their multiplicity are already known
    '''
    not_conference_graph = conference.conference(v, k, l, u) != 0

    det_expected = util.determinant(v, k, l, u)
    for mat in database:
        eigval, eigvec = np.linalg.eig(mat)

        eigval = tuple(int(round(x)) for x in eigval) if not_conference_graph else eigval

        det_from_matrix = np.prod(eigval)
        det_from_matrix = int(round(det_from_matrix))
        assert det_from_matrix == det_expected, "determinant disagree"


@pytest.mark.parametrize('v,k,l,u, database', problems_all)
def test_srg_matrix_identity(v: int, k: int, l: int, u: int, database):
    I = np.identity(v, dtype=int)
    J = np.ones((v, v), dtype=int)
    const = (k - u) * I + u * J
    for mat in database:
        assert np.array_equal(mat @ mat - (l - u) * mat, const)
