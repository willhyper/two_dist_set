from srg import model
from srg.model import Question, Answer, PartialSRG, array
from srg import solver
from srg import database as db
from srg import sorter, canon
import numpy as np
import pytest

problems_all = []

problems = db.list_problems()
for p in problems:
    v,k,l,u = db.extract_vklu(p)
    if v < 20:
        As = db.get_solutions(v,k,l,u)
        problems_all.append((v,k,l,u, As))


def _classes(matrices) -> set:
    '''isomorphism classes of full SRG matrices, via exact canonical form'''
    return {canon.canonical_key(m, leaf_budget=10 ** 7) for m in matrices}


@pytest.mark.parametrize('v,k,l,u, As', problems_all)
def test_solve(v: int, k: int, l: int, u: int, As):
    '''
    solve() yields one representative per isomorphism class, not every vertex
    labeling the database happens to list, so compare isomorphism classes.
    '''
    srg = PartialSRG(solver._seed(v,k,l,u))
    actuals = list(solver.solve(srg))

    assert all(PartialSRG(a).solved() for a in actuals)
    assert _classes(actuals) == _classes(As)


@pytest.mark.parametrize('v,k,l,u, As', problems_all)
def test_solve_without_isomorph_rejection(v: int, k: int, l: int, u: int, As):
    '''
    isomorph_free=False searches every vertex labeling; it must find exactly
    the same isomorphism classes as the pruned search
    '''
    if v > 13: pytest.skip('unpruned search is slow')
    srg = PartialSRG(solver._seed(v,k,l,u))
    actuals = list(solver.solve(srg, isomorph_free=False))
    assert _classes(actuals) == _classes(As)


def _to_seed_labeling(A: np.ndarray, k: int, l: int, a: int, b: int, c: int) -> np.ndarray:
    '''
    relabel the graph A so that it starts like solver._seed does, with vertex a first, its neighbour b second
    and c (a neighbour of a) third:
      vertex 0 = a, vertex 1 = b, then the common neighbours of a and b, then the other neighbours of a,
      then the other neighbours of b, then everyone else; inside each of those groups the neighbours of c
      come first (the order in which Answer.binarize writes a row: ones first within each class of columns)
    '''
    n = A.shape[0]
    adj = lambda x, y: bool(A[x, y])
    rest = [x for x in range(n) if x not in (a, b)]
    groups = [
        [x for x in rest if adj(a, x) and adj(b, x)],
        [x for x in rest if adj(a, x) and not adj(b, x)],
        [x for x in rest if adj(b, x) and not adj(a, x)],
        [x for x in rest if not adj(a, x) and not adj(b, x)],
    ]
    first = 0 if groups[0] else 1
    assert c in groups[first], 'c must be the vertex that comes right after a and b'
    groups[first].remove(c)
    order = [a, b, c] if first == 0 else [a, b]
    for g in groups:
        order += sorted(g, key=lambda x: (not adj(c, x), x))
    if first == 1:
        order.insert(2, c)
    perm = np.array(order)
    return A[perm][:, perm]


@pytest.mark.parametrize('v,k,l,u, As', problems_all)
def test_solve_question(v: int, k: int, l: int, u: int, As):
    '''
    solve_question(seed) enumerates every possible third row. For each stored graph, relabeled to start like
    the seed, its own third row must be one of them.
    '''
    s = solver._seed(v, k, l, u)
    q = Question.from_matrix(s)
    actuals = [tuple(row) for row in solver.solve_question(q)]  # candidates, not necessarily real solutions

    for A in As:
        found = False
        for a in range(v):
            for b in np.flatnonzero(A[a]):
                common = [x for x in range(v) if A[a, x] and A[int(b), x] and x not in (a, int(b))]
                others = [x for x in range(v) if A[a, x] and not A[int(b), x] and x != int(b)]
                c = common[0] if common else others[0]
                R = _to_seed_labeling(A, k, l, a, int(b), c)
                assert np.array_equal(R[0], s[0]) and np.array_equal(R[1], s[1]), 'relabeling must reproduce the seed'
                if tuple(R[2, 3:]) in actuals:
                    found = True
                    break
            if found: break
        assert found, f'no candidate row of solve_question matches a relabeling of a stored solution'


def test_solve_max_solutions_caps_output():
    v, k, l, u = 10, 6, 3, 4

    # isomorph_free=False enumerates every labeling of the (single) graph, so there is more than 1
    srg = PartialSRG(solver._seed(v, k, l, u))
    uncapped = list(solver.solve(srg, max_solutions=None, isomorph_free=False))
    assert len(uncapped) > 1, 'test assumes a quest with more than 1 labeling'

    srg = PartialSRG(solver._seed(v, k, l, u))
    capped = list(solver.solve(srg, max_solutions=1, isomorph_free=False))
    assert len(capped) == 1

    # while the default (isomorph-free) search yields one matrix per graph
    srg = PartialSRG(solver._seed(v, k, l, u))
    assert len(list(solver.solve(srg, max_solutions=None))) == 1


def test_solve_default_max_solutions_is_100():
    import inspect
    assert inspect.signature(solver.solve).parameters['max_solutions'].default == 100
    assert solver.DEFAULT_MAX_SOLUTIONS == 100


def test2():
    A = model.array([[0, 1],
                    [0, 1],
                    [0, 0],
                    [1, 0],
                    [1, 0],
                    [0, 0]])
    b = model.array([4, 4, 0, 4, 4, 0])

    bound = model.array([4, 4])
    ans = Answer(value=model.array([0, -1, 0, 0, -1]), location=model.array([0, 4, 8, 12, 16]), len=20)
    Q = Question(A, b, 8, bound, ans)

    solver.only_1_element_in_row(Q)
    Q._invariant_check()



def test_progress_line_counts_are_consistent(monkeypatch):
    '''pending/reached per number of built rows: a finished exhaustive run has nothing pending'''
    monkeypatch.setattr(solver, 'PROGRESS_INTERVAL', 0.0)  # report after every extended partial matrix
    lines = []
    srg = PartialSRG(solver._seed(21, 10, 5, 4))
    list(solver.solve(srg, max_solutions=None, progress=lines.append))

    assert len(lines) > 5
    assert lines[-1].startswith('finished:')
    per_row = dict(item.split(':') for item in lines[-1].split('rows built: ')[1].split())
    assert all(v.split('/')[0] == '0' for v in per_row.values()), per_row  # nothing left pending

    # mid-run lines: pending never exceeds reached, and pending is 0 exactly where the search has finished
    for line in lines[:-1]:
        for item in line.split('rows built: ')[1].split():
            pend, reach = map(int, item.split(':')[1].split('/'))
            assert 0 <= pend <= reach
