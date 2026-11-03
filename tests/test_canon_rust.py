"""Native certificates must equal the Python reference byte for byte."""
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pytest

from srg import canon, database, solver
from srg import _canon_native

native = canon._rust_canonical
requires_native = pytest.mark.skipif(native is None, reason='run python build_rust.py for native differential tests')


@requires_native
@pytest.mark.parametrize('budget', [-1, 0, 1, 2, 3, 5, 10, 5000])
def test_random_partial_certificates_and_budget_match_reference(budget):
    rng = np.random.default_rng(37)
    for _ in range(120):
        columns = int(rng.integers(2, 18))
        rows = int(rng.integers(1, columns + 1))
        matrix = rng.integers(0, 2, size=(rows, columns), dtype=np.int8)
        block = np.triu(matrix[:, :rows], 1)
        matrix[:, :rows] = block + block.T
        assert native(matrix, budget) == canon._canonical_python(matrix, budget)


@requires_native
def test_banked_graph_prefixes_and_relabelings_match_reference():
    rng = np.random.default_rng(71)
    for problem in database.list_problems():
        quest = database.extract_vklu(problem)
        for matrix in database.get_solutions(*quest):
            v = matrix.shape[0]
            for rows in sorted({2, min(5, v), v // 2, v-1, v}):
                partial = matrix[:rows]
                expected = canon._canonical_python(partial, 5000)
                assert native(partial, 5000) == expected, (quest, rows)
                perm = np.r_[rng.permutation(rows), rows + rng.permutation(v-rows)]
                relabeled = partial[perm[:rows]][:, perm]
                # Budget exhaustion can depend on traversal under relabeling:
                # compare each actual input with the reference at the same budget.
                actual = native(relabeled, 5000)
                assert actual == canon._canonical_python(relabeled, 5000), (quest, rows)
                if actual is not None and expected is not None:
                    assert actual == expected


@requires_native
@pytest.mark.parametrize('dtype', [np.int8, np.uint8, np.int64, np.bool_, np.float64])
def test_numpy_layouts_and_dtypes(dtype):
    matrix = solver._seed(10, 6, 3, 4).astype(dtype)
    inputs = [matrix, np.asfortranarray(matrix), matrix[:, ::-1][:, ::-1],
              np.repeat(matrix, 2, axis=1)[:, ::2]]
    for value in inputs:
        assert native(value, 5000) == canon._canonical_python(value, 5000)


@requires_native
def test_concurrent_native_calls_are_independent():
    matrix = solver._seed(29, 14, 6, 7)
    expected = canon._canonical_python(matrix, 5000)
    assert expected == bytes.fromhex('fbf7efdc90')
    with ThreadPoolExecutor(max_workers=8) as executor:
        assert list(executor.map(lambda _: native(matrix, 5000), range(100))) == [expected]*100


@requires_native
@pytest.mark.parametrize('matrix', [np.array([[0, 256], [256, 0]]),
                                     np.array([[0, -1], [-1, 0]], dtype=np.int8),
                                     np.array([[0, 1], [0, 0]], dtype=np.int8),
                                     np.zeros((3, 2), dtype=np.int8),
                                     np.zeros(3, dtype=np.int8)])
def test_invalid_native_inputs_are_rejected(matrix):
    with pytest.raises(ValueError):
        native(matrix, 5000)


def test_optional_library_and_explicit_backend_selection(monkeypatch):
    monkeypatch.setenv('SRG_CANON_BACKEND', 'python')
    assert _canon_native.load() is None
    monkeypatch.setattr(_canon_native.Path, 'exists', lambda path: False)
    monkeypatch.setenv('SRG_CANON_BACKEND', 'auto')
    assert _canon_native.load() is None
    monkeypatch.setenv('SRG_CANON_BACKEND', 'rust')
    with pytest.raises(ImportError, match='not built'):
        _canon_native.load()
    monkeypatch.setenv('SRG_CANON_BACKEND', 'invalid')
    with pytest.raises(ValueError, match='SRG_CANON_BACKEND'):
        _canon_native.load()
