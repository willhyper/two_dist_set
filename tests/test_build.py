import numpy as np
import pytest

from srg import database as db
from srg.database import build
from srg.model import PartialSRG

PLACEHOLDER = """'''
STATUS: to tackle soon (queued)
Brouwer table srgtab1-50: exists (unique) - Paley(5)
Complement: problem_5_2_0_1 (derive from this one when done)
'''

status = 'todo'  # placeholder

v, k, l, u = 5, 2, 0, 1
solutions: list[str] = []
"""


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(build, 'HERE', str(tmp_path))
    (tmp_path / 'problem_5_2_0_1.py').write_text(PLACEHOLDER)
    return tmp_path


def test_a_placeholder_is_recognised_and_a_result_is_not(tmp_db):
    assert build.is_placeholder(build.problem_path(5, 2, 0, 1))
    build.write_problem(5, 2, 0, 1, [db.get_solutions(5, 2, 0, 1)[0]], 'STATUS: tackled - done')
    assert not build.is_placeholder(build.problem_path(5, 2, 0, 1))


def test_replacing_a_placeholder_keeps_the_table_information_and_the_new_status(tmp_db):
    A = db.get_solutions(5, 2, 0, 1)[0]
    path = build.write_problem(5, 2, 0, 1, [A], 'STATUS: tackled - the search finished: these 1 graph(s) are ALL of them\nsome timing line')
    text = open(path).read()
    assert text.count('STATUS:') == 1 and 'to tackle soon' not in text
    assert 'the search finished: these 1 graph(s) are ALL of them' in text
    assert 'Brouwer table srgtab1-50: exists (unique) - Paley(5)' in text  # kept from the placeholder
    assert 'Complement: problem_5_2_0_1' in text
    assert "status = 'todo'" not in text
    ns = {}
    exec(text, ns)
    from srg.database import codec
    assert len(ns['solutions']) == 1 and np.array_equal(codec.decode(ns['solutions'][0]), A)


def test_write_problem_refuses_a_matrix_that_is_not_an_srg(tmp_db):
    bad = np.zeros((5, 5), dtype=np.int8)
    with pytest.raises(AssertionError):
        build.write_problem(5, 2, 0, 1, [bad], 'STATUS: tackled')


def test_mark_status_rewrites_only_the_status_of_a_placeholder(tmp_db):
    build.mark_status(5, 2, 0, 1, 'tackled - UNDECIDED: no solution found within the 5s time limit', 'details here')
    text = open(build.problem_path(5, 2, 0, 1)).read()
    assert text.count('STATUS:') == 1 and 'UNDECIDED' in text and 'details here' in text
    assert 'Brouwer table srgtab1-50' in text
    assert "status = 'undecided'" in text  # still a placeholder: the empty list proves nothing
    assert build.is_placeholder(build.problem_path(5, 2, 0, 1))


def test_build_records_a_finished_search_as_complete(tmp_db):
    path = build.build(5, 2, 0, 1)
    text = open(path).read()
    assert 'STATUS: tackled - the search finished: these 1 graph(s) are ALL of them' in text
    assert 'Brouwer table srgtab1-50' in text
