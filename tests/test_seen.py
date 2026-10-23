"""Packed keys must retain every exact class, including hash collisions."""
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import pytest
from srg import seen


@pytest.mark.parametrize('width', [0, 1, 5, 32, 128])
def test_full_keys_survive_growth(width):
    table = seen._KeyTable(width)
    keys = [i.to_bytes(width, 'big') for i in range(min(256 ** width, 1000))]
    for key in keys:
        assert table.add(key)
        assert not table.add(key)
    assert table.count == len(keys)
    for key in keys:
        assert not table.add(key)
    assert len(table.data) == table.capacity * (width + 1)


def test_collisions_compare_all_bytes(monkeypatch):
    monkeypatch.setattr(seen, 'hash', lambda key: 0, raising=False)
    table = seen._KeyTable(5)
    keys = [i.to_bytes(5, 'big') for i in range(100)]
    for key in keys:
        assert table.add(key)
    for key in reversed(keys):
        assert not table.add(key)
    assert table.count == len(keys)


def test_row_and_length_groups_are_distinct():
    store = seen.SharedSeen()
    assert store.claim(2, b'\x00')
    assert store.claim(3, b'\x00')
    assert store.claim(2, b'\x00\x00')
    assert not store.claim(2, b'\x00')
    assert store.stats()['keys'] == 3
    assert store.stats()['payload_bytes'] == 4


def test_claims_are_atomic_through_spawn_manager():
    with seen.SeenManager(ctx=multiprocessing.get_context('spawn')) as manager:
        store = manager.SharedSeen()
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: store.claim(4, b'\x00\xff'), range(100)))
        assert sum(results) == 1
        assert store.stats()['keys'] == 1


def test_packed_storage_scales_with_payload():
    store = seen.SharedSeen()
    for i in range(10000):
        assert store.claim(2, i.to_bytes(5, 'big'))
    stats = store.stats()
    assert stats['keys'] == 10000
    assert stats['payload_bytes'] == 50000
    assert stats['table_bytes'] < 16 * stats['keys']
