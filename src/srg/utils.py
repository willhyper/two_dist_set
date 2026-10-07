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


def _field_squares(p: int, n: int) -> np.ndarray:
    '''
    the non-zero squares of GF(p**n). An element is the integer whose base-p digits are the
    coefficients (lowest degree first) of its polynomial, so addition is digit-wise mod p.
    '''
    q = p ** n
    if n == 1:
        return np.unique([(x * x) % p for x in range(1, p)])
    f = _irreducible(p, n)
    squares = set()
    for x in range(1, q):
        digits = [(x // p ** i) % p for i in range(n)]
        prod = [0] * (2 * n - 1)
        for i, a in enumerate(digits):
            for j, b in enumerate(digits):
                prod[i + j] += a * b
        r = _poly_mod(prod, f, p)
        squares.add(sum(c * p ** i for i, c in enumerate(r)))
    return np.array(sorted(squares))


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


def _complement(A: np.ndarray) -> np.ndarray:
    C = (1 - A).astype(A.dtype)
    np.fill_diagonal(C, 0)
    return C


def _paley_matches(v: int, k: int, l: int, u: int):
    pp = prime_power(v)
    if pp is not None and v % 4 == 1 and (k, l, u) == paley_parameters(v)[1:]:
        yield f'Paley({v})', paley(v)


GENERATORS = [_paley_matches]  # each: (v, k, l, u) -> iterator of (name, adjacency matrix)


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

