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
