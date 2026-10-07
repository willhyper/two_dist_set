#!python
#cython: language_level=3

import itertools

import numpy as np

from .model import Question, dtype
from . import pprint

def debug(func):

    def wrapper(Q:Question):
        Q_before = Q.copy()

        result = func(Q)
        if Q == Q_before:
            pprint.blue(f'performing {func.__name__}. No change')
        else:
            print(Q_before)
            pprint.green(f'performing {func.__name__}. reduce to')
            print(Q)


        try:
            Q._invariant_check()
        except AssertionError as e:

            print(Q_before)
            pprint.red(f'performing {func.__name__}. AssertionError!')
            print(Q)

            print()

            raise e

        return result

    return wrapper if __debug__ else func


# ---------------------------------------------------------------------------------------------
# Known constructions of strongly regular graphs. These write a graph down directly from its
# definition (no search), so a problem file can record a graph for a quest the solver cannot
# finish yet. Every generated matrix is still checked with PartialSRG.solved() before it is stored.
# ---------------------------------------------------------------------------------------------

def prime_power(q: int):
    '''(p, n) if q == p**n for a prime p, else None'''
    if q < 2:
        return None
    p = next(d for d in range(2, q + 1) if q % d == 0)  # the smallest divisor of q is prime
    n, r = 0, q
    while r % p == 0:
        r //= p
        n += 1
    return (p, n) if r == 1 else None


def _poly_mod(a: list, f: list, p: int) -> list:
    '''a mod f over GF(p); polynomials are coefficient lists, lowest degree first, f monic'''
    a = a[:]
    n = len(f) - 1
    for i in range(len(a) - 1, n - 1, -1):
        c = a[i] % p
        if c:
            for j in range(n + 1):
                a[i - n + j] = (a[i - n + j] - c * f[j]) % p
    return [x % p for x in a[:n]]


def _irreducible(p: int, n: int) -> list:
    '''a monic irreducible polynomial of degree n over GF(p) (brute force: small fields only)'''
    for low in itertools.product(range(p), repeat=n):
        f = list(low) + [1]
        if n == 1 or all(  # no monic divisor of degree 1 .. n//2
                any(_poly_mod(f, list(g) + [1], p)) for d in range(1, n // 2 + 1)
                for g in itertools.product(range(p), repeat=d)):
            return f
    raise AssertionError('no irreducible polynomial found')


def _field_tables(p: int, n: int):
    '''
    (add, mul): the q x q addition and multiplication tables of GF(q), q = p**n. An element is the
    integer whose base-p digits are the coefficients (lowest degree first) of its polynomial; 0 and 1
    are the field's zero and one.
    '''
    q = p ** n
    digits = np.array([[(x // p ** i) % p for i in range(n)] for x in range(q)])
    powers = p ** np.arange(n)
    add = ((digits[:, None, :] + digits[None, :, :]) % p) @ powers
    if n == 1:
        mul = (np.arange(q)[:, None] * np.arange(q)[None, :]) % p
        return add, mul
    f = _irreducible(p, n)
    mul = np.zeros((q, q), dtype=int)
    for x in range(q):
        for y in range(x, q):
            prod = [0] * (2 * n - 1)
            for i, a_ in enumerate(digits[x]):
                for j, b_ in enumerate(digits[y]):
                    prod[i + j] += int(a_) * int(b_)
            r = _poly_mod(prod, f, p)
            mul[x, y] = mul[y, x] = sum(c * p ** i for i, c in enumerate(r))
    return add, mul


def _field_squares(p: int, n: int) -> np.ndarray:
    '''the non-zero squares of GF(p**n)'''
    _, mul = _field_tables(p, n)
    return np.unique(np.diag(mul)[1:])


def paley_parameters(q: int) -> tuple:
    return q, (q - 1) // 2, (q - 5) // 4, (q - 1) // 4


def paley(q: int) -> np.ndarray:
    '''
    adjacency matrix of the Paley graph on the finite field GF(q): q is a prime power with q = 1 mod 4,
    and i ~ j iff i - j is a non-zero square. It is an SRG(q, (q-1)/2, (q-5)/4, (q-1)/4), and
    self-complementary. Works for primes (5, 13, 29, ...) and prime powers (9, 25, 49, 81, ...).
    '''
    pp = prime_power(q)
    if pp is None or q % 4 != 1:
        raise ValueError(f'Paley graph needs a prime power q = 1 mod 4, got {q}')
    p, n = pp
    digits = np.array([[(x // p ** i) % p for i in range(n)] for x in range(q)])
    diff = ((digits[:, None, :] - digits[None, :, :]) % p) @ (p ** np.arange(n))  # index of i - j
    return np.isin(diff, _field_squares(p, n)).astype(dtype)


def triangular(n: int) -> np.ndarray:
    '''T(n), the line graph of K_n: the 2-subsets of {0..n-1}, adjacent iff they share an element.
    SRG(n(n-1)/2, 2(n-2), n-2, 4).'''
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    A = np.array([[1 if len(set(a) & set(b)) == 1 else 0 for b in pairs] for a in pairs], dtype=dtype)
    return A


def rook(n: int) -> np.ndarray:
    '''the n x n rook's graph K_n x K_n: cells adjacent iff in the same row or column.
    SRG(n^2, 2(n-1), n-2, 2).'''
    cells = [(i, j) for i in range(n) for j in range(n)]
    return np.array([[1 if (a != b and (a[0] == b[0] or a[1] == b[1])) else 0 for b in cells] for a in cells], dtype=dtype)


def latin_square_cyclic(n: int) -> np.ndarray:
    '''Latin square graph of the cyclic Latin square (i + j mod n): cells adjacent iff same row, same
    column or same symbol. SRG(n^2, 3(n-1), n, 6), for every n >= 2.'''
    cells = [(i, j) for i in range(n) for j in range(n)]
    sym = lambda c: (c[0] + c[1]) % n
    return np.array([[1 if (a != b and (a[0] == b[0] or a[1] == b[1] or sym(a) == sym(b))) else 0
                      for b in cells] for a in cells], dtype=dtype)


def net_graph(n: int, k: int) -> np.ndarray:
    '''
    the graph of k parallel classes of the affine plane AG(2, n), n a prime power: the points (x, y) of
    GF(n)^2, adjacent iff on a common line of the chosen classes (x = c, then y = m*x + c for slopes
    m = 0, 1, ...). SRG(n^2, k(n-1), n-2+(k-1)(k-2), k(k-1)), 2 <= k <= n.
    '''
    pp = prime_power(n)
    if pp is None or not 2 <= k <= n:
        raise ValueError(f'net graph needs a prime power n and 2 <= k <= n, got n={n}, k={k}')
    add, mul = _field_tables(*pp)
    neg = np.array([int(np.flatnonzero(add[x] == 0)[0]) for x in range(n)])  # additive inverses
    pts = [(x, y) for x in range(n) for y in range(n)]
    # one invariant per parallel class: points on the same line of that class share its value
    classes = [lambda x, y: x] + [(lambda m: lambda x, y: add[y, neg[mul[m, x]]])(m) for m in range(k - 1)]
    inv = np.array([[c(x, y) for c in classes] for x, y in pts])
    A = (inv[:, None, :] == inv[None, :, :]).any(axis=2)
    np.fill_diagonal(A, False)
    return A.astype(dtype)


def _complement(A: np.ndarray) -> np.ndarray:
    C = (1 - A).astype(A.dtype)
    np.fill_diagonal(C, 0)
    return C


def _paley_matches(v: int, k: int, l: int, u: int):
    pp = prime_power(v)
    if pp is not None and v % 4 == 1 and (k, l, u) == paley_parameters(v)[1:]:
        yield f'Paley({v})', paley(v)


def _isqrt_exact(x: int):
    r = int(round(x ** 0.5))
    return r if r * r == x else None


def _triangular_matches(v: int, k: int, l: int, u: int):
    n = (1 + (1 + 8 * v) ** 0.5) / 2
    if n == int(n) and int(n) >= 4:
        n = int(n)
        if (k, l, u) == (2 * (n - 2), n - 2, 4):
            yield f'Triangular graph T({n})', triangular(n)


def _lattice_matches(v: int, k: int, l: int, u: int):
    n = _isqrt_exact(v)
    if n is None or n < 2:
        return
    if (k, l, u) == (2 * (n - 1), n - 2, 2):
        yield f"Rook's graph K{n} x K{n} (lattice L2({n}))", rook(n)
    for kk in range(3, n + 1):
        if (k, l, u) != (kk * (n - 1), n - 2 + (kk - 1) * (kk - 2), kk * (kk - 1)):
            continue
        if kk == 3:
            yield f'Latin square graph of the cyclic Latin square of order {n}', latin_square_cyclic(n)
        if prime_power(n) is not None:
            yield f'net graph of {kk} parallel classes of AG(2,{n}) (OA({n},{kk}))', net_graph(n, kk)


GENERATORS = [_paley_matches, _triangular_matches, _lattice_matches]  # each: (v, k, l, u) -> iterator of (name, adjacency matrix)


def constructions(v: int, k: int, l: int, u: int) -> list:
    '''
    [(name, matrix), ...]: graphs with these parameters written down from a known construction. The
    complement's parameters are tried too (the complement of an SRG is an SRG), so a quest and its
    complement find the same constructions.
    '''
    cv, ck, cl, cu = v, v - k - 1, v - 2 - 2 * k + u, v - 2 * k + l
    out = []
    for gen in GENERATORS:
        out += list(gen(v, k, l, u))
        if (cv, ck, cl, cu) != (v, k, l, u):  # a self-complementary parameter set would only repeat itself
            out += [(f'complement of {name}', _complement(A)) for name, A in gen(cv, ck, cl, cu)]
    return out

