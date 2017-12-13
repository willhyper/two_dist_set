__author__ = 'chaoweichen'

from two_dist_set.srg import SRG
from two_dist_set import strong_graph
from two_dist_set.problem_database import *

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
    not_conference_graph = strong_graph.conference(v, k, l, u) != 0

    em_expected = {e: m for e, m in strong_graph.eig(v, k, l, u)}

    det_expected = strong_graph.determinant(v, k, l, u)
    print('expected determinant', det_expected)
    print('expected (eigenvalue, multiplicity)', em_expected)

    s = SRG(v, k, l, u)
    seed = strong_graph.generate_seed(v, k, l, u)
    s.add(seed)
    for mat in strong_graph.generate(s):
        eigval, eigvec = np.linalg.eig(mat)

        eigval = tuple(int(round(x)) for x in eigval) if not_conference_graph else eigval

        det = 1
        for e in eigval: det *= e
        det = int(round(det))
        assert det == det_expected, "determinant disagree"

        c = Counter(eigval)
        em_actual = {k: c.get(k) for k in sorted(c.keys(), reverse=True)}

        print('actual   (eigenvalue, multiplicity)', em_actual)
