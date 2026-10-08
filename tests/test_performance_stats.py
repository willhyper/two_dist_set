import importlib
import re

import pytest

from srg import database as db

PROBLEMS = sorted(db.list_problems())


def _module(name):
    return importlib.import_module('srg.database.' + name)


@pytest.mark.parametrize('name', PROBLEMS)
def test_every_problem_file_defines_the_performance_variables(name):
    m = _module(name)
    for var in ('cpu_sec', 'wall_clock_sec'):
        value = getattr(m, var)  # an AttributeError here means the file was never migrated
        assert value is None or (isinstance(value, (int, float)) and value > 0), (name, var, value)


@pytest.mark.parametrize('name', PROBLEMS)
def test_a_placeholder_has_no_performance_numbers(name):
    m = _module(name)
    if getattr(m, 'status', None) is not None:  # 'todo' / 'undecided': nothing finished
        assert m.cpu_sec is None and m.wall_clock_sec is None


@pytest.mark.parametrize('name', PROBLEMS)
def test_the_docstring_carries_no_timing_lines(name):
    # timings live in the variables (fastest finished run only); the docstring is narrative
    doc = (_module(name).__doc__ or '')
    for line in doc.split('\n'):
        assert not re.match(r'^[\d.,e+-]+s( CPU| wall-clock|\.)', line), (name, line)
        assert not line.startswith('Intel') and 'Apple M1' not in line, (name, line)


def test_the_stored_numbers_cover_the_solved_problems_that_were_timed():
    timed = [n for n in PROBLEMS if _module(n).cpu_sec is not None or _module(n).wall_clock_sec is not None]
    assert len(timed) >= 25
