from two_dist_set.util import determinant

__author__ = 'chaoweichen'

from two_dist_set import strong_graph, conference, util
from two_dist_set.problem_database import *
from two_dist_set import srg

import numpy as np
from collections import Counter

import pytest

problems = []
problems.append(problem_4_2_0_2)
problems.append(problem_5_2_0_1)
problems.append(problem_6_3_0_3)
problems.append(problem_6_4_2_4)
problems.append(problem_9_4_1_2)
problems.append(problem_10_3_0_1)
problems.append(problem_10_6_3_4)
problems.append(problem_12_6_0_6)
problems.append(problem_13_6_2_3)
problems.append(problem_15_8_4_4)
problems.append(problem_16_5_0_2)
problems.append(problem_16_6_2_2)
problems.append(problem_16_9_4_6)
problems.append(problem_16_10_6_6)
problems.append(problem_17_8_3_4)
# problems.append()
# problems.append()
# problems.append(problem_21_10_5_4)

@pytest.mark.parametrize('v,k,l,u, expected', problems)
def test_strong(v, k, l, u, expected):
    not_conference_graph = conference.conference(v, k, l, u) != 0

    em_expected = {e: m for e, m in util.eig(v, k, l, u)}

    det_expected = util.determinant(v, k, l, u)
    print('expected determinant', det_expected)
    print('expected (eigenvalue, multiplicity)', em_expected)

    seed = util.generate_seed(v, k, l, u)

    for mat in srg.solve(seed):
        eigval, eigvec = np.linalg.eig(mat)

        eigval = tuple(int(round(x)) for x in eigval) if not_conference_graph else eigval

        det = np.prod(eigval)
        det = int(round(det))
        assert det == det_expected, "determinant disagree"

        c = Counter(eigval)
        em_actual = {k: c.get(k) for k in sorted(c.keys(), reverse=True)}

        print('actual   (eigenvalue, multiplicity)', em_actual)



@pytest.mark.parametrize('v,k,l,u, expected', problems)
def test_matrix_identity(v: int, k: int, l: int, u: int, expected):
    I = np.identity(v, dtype=np.int)
    J = np.ones((v, v), dtype=np.int)
    const = (k - u) * I + u * J
    for mat in expected:
        assert np.array_equal(mat @ mat - (l - u) * mat, const)

@pytest.mark.parametrize('v,k,l,u,expected', problems)
def test_database(v, k, l, u, expected):
    seed = util.generate_seed(v, k, l, u)

    actual = list(srg.solve(seed))
    assert len(actual) == len(expected)

    for g, e in zip(actual, expected):
        assert np.array_equal(g, e)


@pytest.mark.parametrize('v,k,l,u,expected', problems)
def test_adj_matrix_property(v, k, l, u, expected):
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
    :param expected: a list of matrix
    :return: None
    '''
    for mat in expected:
        for ri in range(1, v-1):

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

