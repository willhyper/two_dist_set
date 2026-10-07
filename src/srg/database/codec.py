'''
Plain-text form of an adjacency matrix, as stored in problem_*.py:

    solutions: list[str] = [
    """
    0110
    1001
    1001
    0110
    """,
    ]

one row per line, one character ('0' or '1') per entry. encode()/decode() convert
to and from the numpy int8 matrices the rest of the package works with.
'''
import numpy as np

from ..model import dtype


def encode(A: np.ndarray) -> str:
    '''matrix -> text block (one 0/1 row per line, framed by newlines)'''
    A = np.asarray(A)
    assert A.ndim == 2, 'expected a 2-D matrix'
    assert np.isin(A, (0, 1)).all(), 'adjacency matrices hold only 0 and 1'
    return '\n' + '\n'.join(''.join('1' if x else '0' for x in row) for row in A) + '\n'


def decode(text: str) -> np.ndarray:
    '''text block -> int8 matrix. Blank lines and spaces/commas between entries are ignored.'''
    rows = []
    for line in text.splitlines():
        row = line.replace(' ', '').replace(',', '').strip()
        if row:
            rows.append(row)
    if not rows:
        raise ValueError('empty matrix text')
    width = len(rows[0])
    for r, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(f'row {r} has {len(row)} entries, expected {width}')
        if set(row) - {'0', '1'}:
            raise ValueError(f'row {r} has characters other than 0 and 1: {row!r}')
    return np.array([[int(c) for c in row] for row in rows], dtype=dtype)
