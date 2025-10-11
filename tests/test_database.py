__author__ = 'Chao-Wei Chen, madmath0902@gmail.com'

from srg import utils
from srg import database as db
from srg import srg
import numpy as np

import pytest

problems_all = []

problems = db.list_problems()
for p in problems:
    v,k,l,u = db.extract_vklu(p)
    As = db.get_solutions(v,k,l,u)
    for A in As: # A is adjacency matrix
        problems_all.append((v,k,l,u, A))

@pytest.mark.parametrize('v,k,l,u, A', problems_all)
def test_A_shape_len_is_v(v: int, k: int, l: int, u: int, A : np.ndarray):
    '''
    A is a square matrix of size v
    '''
    assert A.shape[0] == A.shape[1] == v

@pytest.mark.parametrize('v,k,l,u, A', problems_all)
def test_A_element_0_or_1(v: int, k: int, l: int, u: int, A : np.ndarray):
    '''
    each element is either 0 or 1
    '''
    assert np.all(np.isin(A, [0,1]))

@pytest.mark.parametrize('v,k,l,u, A', problems_all)
def test_A_symmetric(v: int, k: int, l: int, u: int, A : np.ndarray):
    '''
    A is symmetric
    '''
    assert np.array_equal(A, A.T)
    
@pytest.mark.parametrize('v,k,l,u, A', problems_all)
def test_matrix_property_k(v: int, k: int, l: int, u: int, A : np.ndarray):
    '''
    each row has k 1's
    '''
    row_sum = A.sum(axis=1)        
    assert np.all(row_sum == k)

@pytest.mark.parametrize('v,k,l,u, A', problems_all)
def test_A_property_lu(v: int, k: int, l: int, u: int, A : np.ndarray):
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
    
    for ri in range(1, v - 1):
        mr = A[:ri, :]
        m_left, pivot, m_right = mr[:, :ri], mr[:, ri], mr[:, ri+1:] 
        lu = [l if e else u for e in pivot]
        solution = A[ri, ri + 1:]
        assert np.array_equal(m_left @ pivot + m_right @ solution, lu)


@pytest.mark.parametrize('v,k,l,u, A', problems_all)
def test_A_determinant(v: int, k: int, l: int, u: int, A : np.ndarray):
    '''
    determinant can be obtained by two ways, so we want them agree with each other

    det_from_matrix, calculated from matrix, from database
    det_expected, derived from SRG requirements: eigenvalues and their multiplicity are already known
    '''
    not_conference_graph = utils.conference(v, k, l, u) != 0

    det_expected = utils.determinant(v, k, l, u)
    
    eigval, eigvec = np.linalg.eig(A)

    eigval = tuple(int(np.round(x)) for x in eigval) if not_conference_graph else eigval

    det_from_matrix = np.prod(eigval)
    det_from_matrix = int(np.round(det_from_matrix))
    assert det_from_matrix == det_expected, "determinant disagree"


@pytest.mark.parametrize('v,k,l,u, A', problems_all)
def test_Acomplement_is_srg(v: int, k: int, l: int, u: int, A : np.ndarray):
    '''
    the complement of A is also an SRG
    '''
    I = srg.identity(v)
    J = srg.ones((v, v))
    const = (k - u) * I + u * J
    
    assert np.array_equal(A @ A - (l - u) * A, const)

    Ac = utils.complement(A)
    #Ac = map(sorter.maximize, Ac) # does not matter do maximize or not
    cv, ck, cl, cu = utils.complement_vklu(v,k,l,u)
    cconst = (ck - cu) * I + cu * J
    
    assert np.array_equal(Ac @ Ac - (cl - cu) * Ac, cconst)