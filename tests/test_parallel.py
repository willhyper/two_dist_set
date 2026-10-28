"""solve_parallel must find exactly the isomorphism classes the serial solver finds."""
import pytest

from srg import canon, parallel, solver
from srg.model import PartialSRG


def classes(gen):
    return {canon.canonical_key(m, 10 ** 7) for m in gen}


@pytest.mark.parametrize('quest', [(13, 6, 2, 3), (16, 6, 2, 2), (15, 6, 1, 3), (21, 10, 5, 4)])
@pytest.mark.parametrize('slice_seconds', [0.02, 20])
def test_same_classes_as_serial(quest, slice_seconds):
    start = PartialSRG(solver._seed(*quest))
    serial = classes(solver.solve(start, max_solutions=None))
    par = classes(parallel.solve_parallel(start, max_solutions=None, workers=2, slice_seconds=slice_seconds))
    assert par == serial
    assert all(PartialSRG(m).solved() for m in parallel.solve_parallel(start, max_solutions=3, workers=2))


def test_no_solution_quest_is_exhausted():
    start = PartialSRG(solver._seed(21, 10, 4, 5))
    msgs = []
    assert list(parallel.solve_parallel(start, max_solutions=None, workers=2, progress=msgs.append)) == []
    assert msgs[-1].startswith('finished')


def test_cap_stops_the_search():
    start = PartialSRG(solver._seed(16, 6, 2, 2))
    assert len(list(parallel.solve_parallel(start, max_solutions=1, workers=2))) == 1


def test_not_isomorph_free_still_works():
    start = PartialSRG(solver._seed(13, 6, 2, 3))
    assert len(list(parallel.solve_parallel(start, max_solutions=2, workers=2, isomorph_free=False))) == 2


def test_relabelings_share_one_stored_key_and_record_each_hit(monkeypatch):
    from collections import defaultdict
    import numpy as np
    from srg.seen import SharedSeen
    store = SharedSeen()
    matrix = solver._seed(13, 6, 2, 3)
    permutation = np.r_[1, 0, np.arange(12, 1, -1)]
    relabeled = matrix[permutation[:2]][:, permutation]
    assert not np.array_equal(matrix, relabeled)
    counts = defaultdict(lambda: [0, 0])
    local = set()
    assert parallel._fresh_shared(local, store, 2, matrix, True, counts)
    assert not parallel._fresh_shared(local, store, 2, relabeled, True, counts)
    # A new worker slice has an empty local set but finds the shared key.
    assert not parallel._fresh_shared(set(), store, 2, relabeled, True, counts)
    monkeypatch.setattr(canon, 'canonical_key', lambda m: None)
    assert parallel._fresh_shared(local, store, 2, matrix, True, counts)
    store.record_local(dict(counts))
    stats = store.stats()
    assert stats['keys'] == 1
    assert stats['local_duplicate_hits'] == 1
    assert stats['shared_duplicate_hits'] == 1
    assert stats['canonicalization_skips'] == 1
    assert stats['candidates'] == 4


def test_final_metrics_survive_manager_shutdown_and_match_database():
    import json
    from srg import database
    start = PartialSRG(solver._seed(16, 6, 2, 2))
    snapshots, lines = [], []
    solutions = list(parallel.solve_parallel(
        start, max_solutions=None, workers=2, slice_seconds=0.02,
        dedup_progress=snapshots.append, progress=lines.append))
    assert all(PartialSRG(m).solved() for m in solutions)
    assert classes(solutions) == classes(database.get_solutions(16, 6, 2, 2))
    final = snapshots[-1]
    assert final['state'] == 'finished'
    assert final['keys'] > 0
    assert final['duplicate_hits'] >= 0
    assert final['candidates'] == final['keys'] + final['duplicate_hits'] + final['canonicalization_skips']
    assert final['keys'] == sum(row['keys'] for row in final['by_rows'].values())
    assert final['payload_bytes'] == sum(g['keys'] * g['key_bytes'] for g in final['by_key_size'])
    assert all(a['keys'] <= b['keys'] for a, b in zip(snapshots, snapshots[1:]))
    assert json.loads(lines[-1].split('; dedup: ')[1])['keys'] == final['keys']


@pytest.mark.parametrize('options', [{'share_seen': False}, {'isomorph_free': False}])
def test_unavailable_shared_metrics_are_not_reported_as_zero(options):
    snapshots = []
    start = PartialSRG(solver._seed(5, 2, 0, 1))
    assert list(parallel.solve_parallel(start, workers=2, dedup_progress=snapshots.append, **options))
    assert snapshots == []
