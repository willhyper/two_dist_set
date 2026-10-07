import numpy as np
import pytest

from srg import canon, utils
from srg import database as db
from srg.database import build
from srg.model import PartialSRG, SRGProperties

# every Paley graph in Brouwer's tables up to 100 vertices: primes and prime powers q = 1 mod 4
PALEY_Q = [5, 9, 13, 17, 25, 29, 37, 41, 49, 53, 61, 73, 81, 89, 97]


@pytest.mark.parametrize('q', PALEY_Q)
def test_paley_is_an_srg_with_the_right_parameters(q):
    A = utils.paley(q)
    assert A.shape == (q, q) and A.dtype == np.int8
    assert np.array_equal(A, A.T) and not A.diagonal().any()
    assert SRGProperties.from_matrix(A).vklu == utils.paley_parameters(q) == (q, (q - 1) // 2, (q - 5) // 4, (q - 1) // 4)
    assert PartialSRG(A).solved()


@pytest.mark.parametrize('q', PALEY_Q)
def test_paley_is_self_complementary(q):
    A = utils.paley(q)
    assert canon.canonical_key(A) == canon.canonical_key(utils._complement(A))


@pytest.mark.parametrize('bad', [4, 7, 15, 21, 33, 45, 1])
def test_paley_rejects_non_prime_powers_and_wrong_residues(bad):
    with pytest.raises(ValueError):
        utils.paley(bad)


@pytest.mark.parametrize('n,expected', [(2, (2, 1)), (9, (3, 2)), (25, (5, 2)), (81, (3, 4)), (97, (97, 1)),
                                       (6, None), (12, None), (1, None)])
def test_prime_power(n, expected):
    assert utils.prime_power(n) == expected


def test_prime_power_field_uses_a_real_field_not_integers_mod_q():
    # Z/9 is not a field: using i - j mod 9 would give a different (non-SRG) graph than GF(9)
    A = utils.paley(9)
    mod9 = np.array([[1 if ((i - j) % 9) in {1, 4, 7} else 0 for j in range(9)] for i in range(9)], dtype=np.int8)
    assert PartialSRG(A).solved()
    assert not PartialSRG(mod9).solved()


def test_constructions_finds_the_right_family_for_a_quest_and_nothing_for_others():
    assert [n for n, _ in utils.constructions(29, 14, 6, 7)] == ['Paley(29)']
    assert [n for n, _ in utils.constructions(28, 12, 6, 4)] == ['Triangular graph T(8)']
    assert utils.constructions(35, 16, 6, 8) == []  # no generator for this one (yet)


def test_recorded_paley_problems_hold_the_generated_graph():
    for q in PALEY_Q:
        sols = db.get_solutions(*utils.paley_parameters(q))
        keys = {canon.canonical_key(m, 10 ** 7) for m in sols}
        assert canon.canonical_key(utils.paley(q)) in keys, f'Paley({q}) missing from its problem file'
