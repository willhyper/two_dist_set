import random

from srg import canon, database as db, solver
from srg.model import PartialSRG


def _classes(ms):
    return {canon.canonical_key(m, 10 ** 6) for m in ms}


def test_restarts_find_valid_solutions():
    got = list(solver.solve_restarts(PartialSRG(solver._seed(16, 6, 2, 2)), max_solutions=2, first_budget=5, seed=3))
    assert len(got) == 2 and all(PartialSRG(m).solved() for m in got)
    assert _classes(got) == _classes(db.get_solutions(16, 6, 2, 2))  # both graphs of SRG(16,6,2,2)


def test_a_tiny_budget_still_terminates_correctly_when_the_tree_is_small():
    # SRG(10,6,3,4) has one graph; with a tiny first budget the rounds grow until one exhausts the tree
    got = list(solver.solve_restarts(PartialSRG(solver._seed(10, 6, 3, 4)), max_solutions=None, first_budget=2, growth=2.0))
    assert len(got) == 1


def test_a_non_existent_quest_terminates_only_by_exhausting_the_tree():
    got = list(solver.solve_restarts(PartialSRG(solver._seed(28, 9, 0, 4)), max_solutions=None, first_budget=50, growth=3.0))
    assert got == []  # the search space was exhausted in some round, which is a proof, as with solve()


def test_node_budget_and_info():
    info = {}
    list(solver.solve(PartialSRG(solver._seed(17, 8, 3, 4)), max_solutions=None, node_budget=3, info=info, rng=random.Random(0)))
    assert info['explored'] == 3 and not info['exhausted']
