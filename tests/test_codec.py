import numpy as np
import pytest

from srg import database as db
from srg.database import codec
from srg.model import array


def test_encode_looks_like_a_grid():
    A = array([[0, 1, 1, 0],
               [1, 0, 0, 1],
               [1, 0, 0, 1],
               [0, 1, 1, 0]])
    assert codec.encode(A) == '\n0110\n1001\n1001\n0110\n'


def test_decode_is_tolerant_of_layout():
    expected = array([[0, 1], [1, 0]])
    assert np.array_equal(codec.decode('01\n10'), expected)
    assert np.array_equal(codec.decode('\n   01  \n\n 10\n'), expected)
    assert np.array_equal(codec.decode('0 1\n1 0'), expected)
    assert np.array_equal(codec.decode('0,1\n1,0'), expected)


def test_decode_returns_model_dtype():
    assert codec.decode('01\n10').dtype == array([0]).dtype


@pytest.mark.parametrize('bad', ['', '  \n ', '01\n1', '0a\n10', '02\n20'])
def test_decode_rejects_malformed_text(bad):
    with pytest.raises(ValueError):
        codec.decode(bad)


def test_encode_rejects_non_binary():
    with pytest.raises(AssertionError):
        codec.encode(array([[0, 2], [2, 0]]))


def test_roundtrip_every_database_solution():
    n = 0
    for p in db.list_problems():
        for A in db.get_solutions(*db.extract_vklu(p)):
            assert np.array_equal(codec.decode(codec.encode(A)), A)
            n += 1
    assert n >= 30  # one canonical matrix per graph, 30+ problem files have solutions


def test_problem_files_store_text_not_arrays():
    import importlib
    m = importlib.import_module('srg.database.problem_10_6_3_4')
    assert all(isinstance(s, str) for s in m.solutions)
    assert db.get_solutions(10, 6, 3, 4)[0].shape == (10, 10)
