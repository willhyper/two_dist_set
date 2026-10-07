import importlib.util
import os

import pytest

from srg import database as db

# the checker lives with the studies (it is also a script): load it by path
_spec = importlib.util.spec_from_file_location(
    'reachability', os.path.join(os.path.dirname(__file__), '..', 'studies', 'reachability.py'))
reachability = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reachability)

SMALL = [(q, i) for q in sorted(tuple(db.extract_vklu(p)) for p in db.list_problems()) if q[0] <= 21
         for i in range(len(db.get_solutions(*q)))]


@pytest.mark.parametrize('q,i', SMALL)
def test_every_row_of_a_known_graph_is_reachable(q, i):
    '''
    Rebuild a known SRG row by row the way the solver does: at each level the true next row must be among the
    candidates solver.advance enumerates (up to isomorphism), and the spectral pruning must accept the prefix.
    If any enumeration or pruning step lost a real solution, a known graph would fail here.
    '''
    good, where = reachability.reach(db.get_solutions(*q)[i], q)
    assert good, f'SRG{q} graph {i}: the true row {abs(where)} is not reachable ({"pruned" if where < 0 else "not enumerated"})'


def test_the_check_can_fail():
    '''
    negative control: a regular graph that is NOT an SRG(13,6,2,3) (a double edge swap away from the first rows
    of Paley(13)) cannot be rebuilt row by row, so the check must report a failure
    '''
    import itertools
    import numpy as np
    from srg.model import PartialSRG

    A0 = db.get_solutions(13, 6, 3 - 1, 3)[0]
    b = int(np.flatnonzero(A0[0])[0])
    others = [x for x in range(13) if x not in (0, b)]
    broken = None
    for x, y, z, w in itertools.permutations(others, 4):
        if A0[x, y] and A0[z, w] and not A0[x, z] and not A0[y, w]:
            A = A0.copy()
            for p, q, val in [(x, y, 0), (z, w, 0), (x, z, 1), (y, w, 1)]:
                A[p, q] = A[q, p] = val
            if not PartialSRG(A).solved():
                broken = A
                break
    assert broken is not None and (broken.sum(axis=1) == 6).all()  # still 6-regular, just not strongly regular
    good, where = reachability.reach(broken, (13, 6, 2, 3))
    assert not good
