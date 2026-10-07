import numpy as np
import pytest

from srg import canon, solver
from srg.model import PartialSRG


def _run(vklu, checkpoint=None, crash_after=None, **kw):
    '''solve, optionally "crashing" (KeyboardInterrupt) on the crash_after-th progress line'''
    calls = []

    def progress(msg):
        calls.append(msg)
        if crash_after is not None and len(calls) == crash_after:
            raise KeyboardInterrupt

    out = list(solver.solve(PartialSRG(solver._seed(*vklu)), progress=progress, checkpoint=checkpoint, **kw))
    return out, calls


def _classes(ms):
    return {canon.canonical_key(m, 10 ** 7) for m in ms}


@pytest.fixture(autouse=True)
def checkpoint_every_advance(monkeypatch):
    monkeypatch.setattr(solver, 'CHECKPOINT_INTERVAL', 0.0)
    monkeypatch.setattr(solver, 'PROGRESS_INTERVAL', 0.0)  # a progress line after every advance


@pytest.mark.parametrize('vklu', [(16, 6, 2, 2), (13, 6, 2, 3), (21, 10, 5, 4)])
def test_interrupted_run_resumes_to_the_same_answer(vklu, tmp_path):
    expected, calls = _run(vklu)
    ckpt = str(tmp_path / 'c.npz')

    # crash at several different points of the run, including mid-level
    # (not before the first checkpoint exists, which is written after the first advance)
    for crash_at in {4, len(calls) // 3, len(calls) // 2, len(calls) - 2}:
        path = ckpt + str(crash_at)
        with pytest.raises(KeyboardInterrupt):
            _run(vklu, checkpoint=path, crash_after=crash_at)

        resumed, rcalls = _run(vklu, checkpoint=path)
        assert any('resumed from' in c for c in rcalls)
        assert _classes(resumed) == _classes(expected)
        assert all(PartialSRG(m).solved() for m in resumed)
        assert len(rcalls) < len(calls)  # it really skipped work


def test_resume_survives_repeated_crashes(tmp_path):
    vklu, path = (21, 10, 5, 4), str(tmp_path / 'c.npz')
    expected, _ = _run(vklu)
    for _ in range(4):
        with pytest.raises(KeyboardInterrupt):
            _run(vklu, checkpoint=path, crash_after=6)
    resumed, _ = _run(vklu, checkpoint=path)
    assert _classes(resumed) == _classes(expected)


def test_finished_checkpoint_replays_without_searching(tmp_path):
    vklu, path = (16, 6, 2, 2), str(tmp_path / 'c.npz')
    first, _ = _run(vklu, checkpoint=path)
    again, calls = _run(vklu, checkpoint=path)
    assert _classes(again) == _classes(first) and len(again) == len(first)
    assert len(calls) == 1 and 'finished' in calls[0]  # only the "resumed" line, no search


def test_checkpoint_of_a_different_quest_is_ignored(tmp_path):
    path = str(tmp_path / 'c.npz')
    _run((13, 6, 2, 3), checkpoint=path)
    out, calls = _run((16, 6, 2, 2), checkpoint=path)  # same file, other quest
    assert not any('resumed' in c for c in calls)
    assert _classes(out) == _classes(_run((16, 6, 2, 2))[0])


def test_checkpoint_with_other_settings_or_version_is_ignored(tmp_path, monkeypatch):
    vklu, path = (13, 6, 2, 3), str(tmp_path / 'c.npz')
    _run(vklu, checkpoint=path, max_solutions=1)
    _, calls = _run(vklu, checkpoint=path, max_solutions=None)
    assert not any('resumed' in c for c in calls)

    monkeypatch.setattr(solver, 'CHECKPOINT_VERSION', solver.CHECKPOINT_VERSION + 1)
    _, calls = _run(vklu, checkpoint=path, max_solutions=None)
    assert not any('resumed' in c for c in calls)


def test_capped_run_checkpoint_is_final(tmp_path):
    vklu, path = (16, 6, 2, 2), str(tmp_path / 'c.npz')
    first, _ = _run(vklu, checkpoint=path, max_solutions=1)
    assert len(first) == 1
    again, calls = _run(vklu, checkpoint=path, max_solutions=1)
    assert len(again) == 1 and 'finished' in calls[0]
