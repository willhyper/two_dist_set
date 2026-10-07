import numpy as np
import pytest

from srg import canon, utils
from srg import database as db
from srg.model import PartialSRG, SRGProperties


def _check(A, vklu):
    assert A.dtype == np.int8 and np.array_equal(A, A.T) and not A.diagonal().any()
    assert tuple(int(x) for x in SRGProperties.from_matrix(A).vklu) == vklu
    assert PartialSRG(A).solved()


@pytest.mark.parametrize('n', [4, 5, 6, 7, 8, 9, 10, 11, 12])
def test_triangular(n):
    _check(utils.triangular(n), (n * (n - 1) // 2, 2 * (n - 2), n - 2, 4))


@pytest.mark.parametrize('n', [3, 4, 5, 6, 7, 8, 9, 10])
def test_rook_and_cyclic_latin_square(n):
    _check(utils.rook(n), (n * n, 2 * (n - 1), n - 2, 2))
    _check(utils.latin_square_cyclic(n), (n * n, 3 * (n - 1), n, 6))


@pytest.mark.parametrize('n,k', [(4, 2), (4, 3), (5, 3), (5, 4), (7, 3), (7, 5), (8, 4), (8, 5), (9, 4), (9, 6)])
def test_net_graph(n, k):
    _check(utils.net_graph(n, k), (n * n, k * (n - 1), n - 2 + (k - 1) * (k - 2), k * (k - 1)))


@pytest.mark.parametrize('q', [2, 3, 4])
def test_symplectic_gq(q):
    _check(utils.symplectic_gq(q), ((q + 1) * (q * q + 1), q * (q + 1), q - 1, q + 1))


def test_hyperoval_gq():
    _check(utils.hyperoval_gq(4), (64, 18, 2, 6))
    with pytest.raises(ValueError):
        utils.hyperoval_gq(3)


def test_hoffman_singleton_has_girth_5():
    A = utils.hoffman_singleton()
    _check(A, (50, 7, 0, 1))
    # lambda = 0 means no triangles, mu = 1 means no 4-cycles: girth 5, the defining property
    assert np.trace(np.linalg.matrix_power(A.astype(int), 3)) == 0
    assert np.trace(np.linalg.matrix_power(A.astype(int), 4)) == 50 * (7 * 7 + 7 * 6)  # closed 4-walks: only back-and-forth


@pytest.mark.parametrize('q,m,elliptic,vklu', [
    (2, 2, True, (16, 5, 0, 2)), (2, 3, True, (64, 27, 10, 12)), (2, 3, False, (64, 35, 18, 20)), (3, 2, True, (81, 20, 1, 6)),
])
def test_affine_polar(q, m, elliptic, vklu):
    _check(utils.affine_polar(q, m, elliptic), vklu)


def test_hermitian_u42():
    _check(utils.hermitian_u42(), (45, 12, 3, 3))


@pytest.mark.parametrize('n', [13, 15, 19, 21, 25])
def test_steiner_triple_system_and_its_block_graph(n):
    blocks = utils.steiner_triple_system(n)
    assert len(blocks) == n * (n - 1) // 6
    pairs = [p for b in blocks for p in ((b[0], b[1]), (b[0], b[2]), (b[1], b[2]))]
    assert len(set(pairs)) == len(pairs) == n * (n - 1) // 2, 'every pair of points lies in exactly one block'
    _check(utils.block_graph(blocks), (n * (n - 1) // 6, 3 * (n - 3) // 2, (n + 3) // 2, 9))


@pytest.mark.parametrize('bad', [7, 9, 11, 14])
def test_steiner_triple_system_rejects_unsupported_orders(bad):
    with pytest.raises(ValueError):
        utils.steiner_triple_system(bad)


@pytest.mark.parametrize('vklu,fragment', [
    ((85, 20, 3, 5), 'W(4)'), ((64, 18, 2, 6), 'hyperoval'), ((50, 7, 0, 1), 'Hoffman'), ((45, 12, 3, 3), 'U(4,2)'),
    ((81, 20, 1, 6), 'VO-(4,3)'), ((64, 27, 10, 12), 'VO-(6,2)'), ((57, 24, 11, 9), 'STS(19)'),
    ((28, 12, 6, 4), 'T(8)'), ((97, 48, 23, 24), 'Paley(97)'),
])
def test_registry_finds_each_family_by_parameters_and_its_complement(vklu, fragment):
    found = utils.constructions(*vklu)
    assert any(fragment in name for name, _ in found), [n for n, _ in found]
    for _, A in found:
        _check(A, vklu)
    v, k, l, u = vklu
    comp = utils.constructions(v, v - k - 1, v - 2 - 2 * k + u, v - 2 * k + l)  # the complement's quest
    assert comp and all(PartialSRG(A).solved() for _, A in comp)


def test_registry_does_not_invent_graphs():
    for vklu in [(36, 15, 6, 6), (36, 14, 4, 6), (63, 30, 13, 15), (96, 20, 4, 4), (77, 16, 0, 4)]:
        names = [n for n, _ in utils.constructions(*vklu)]
        if vklu == (36, 15, 6, 6):  # the one with a Latin square graph
            assert names and 'Latin square' in names[0]
        else:
            assert names == [], f'{vklu}: {names}'


def test_every_constructible_problem_file_holds_a_constructed_graph():
    '''the recorded problem files really contain the generated graphs (up to isomorphism)'''
    n = 0
    for p in db.list_problems():
        q = tuple(db.extract_vklu(p))
        found = utils.constructions(*q)
        if not found:
            continue
        have = {canon.canonical_key(m, 10 ** 7) for m in db.get_solutions(*q)}
        for name, A in found:
            assert canon.canonical_key(A, 10 ** 7) in have, f'{q}: {name} is not in its problem file'
        n += 1
    assert n >= 80
