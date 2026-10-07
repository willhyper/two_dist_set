#!python
#cython: language_level=3

import itertools

import numpy as np

from .model import Question, SRGProperties, dtype
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


def _field(q: int):
    '''(add, mul, neg, inv): the operation tables of GF(q) (elements 0..q-1, 0 and 1 the zero and one)'''
    p, n = prime_power(q)
    add, mul = _field_tables(p, n)
    neg = np.array([int(np.flatnonzero(add[x] == 0)[0]) for x in range(q)])
    inv = np.array([0] + [int(np.flatnonzero(mul[x] == 1)[0]) for x in range(1, q)])
    return add, mul, neg, inv


def _projective_points(q: int, dim: int, mul, inv) -> list:
    '''the points of PG(dim-1, q): non-zero vectors scaled so that the first non-zero coordinate is 1'''
    pts = []
    for v in itertools.product(range(q), repeat=dim):
        nz = next((c for c in v if c), 0)
        if nz == 1:
            pts.append(v)
    return pts


def symplectic_gq(q: int) -> np.ndarray:
    '''
    collinearity graph of the symplectic generalized quadrangle W(q): the points of PG(3,q), two adjacent
    iff orthogonal for w(x,y) = x0 y1 - x1 y0 + x2 y3 - x3 y2. SRG((q+1)(q^2+1), q(q+1), q-1, q+1).
    '''
    add, mul, neg, inv = _field(q)
    pts = _projective_points(q, 4, mul, inv)
    P = np.array(pts)

    def w(x, y):
        s = add[mul[x[0], y[1]], neg[mul[x[1], y[0]]]]
        return add[s, add[mul[x[2], y[3]], neg[mul[x[3], y[2]]]]]

    n = len(pts)
    A = np.zeros((n, n), dtype=dtype)
    for i in range(n):
        for j in range(i + 1, n):
            if w(pts[i], pts[j]) == 0:
                A[i, j] = A[j, i] = 1
    return A


def hyperoval_gq(q: int) -> np.ndarray:
    '''
    the generalized quadrangle T2*(O) = GQ(q-1, q+1) for q = 2^h >= 4: vertices GF(q)^3 (adding vectors),
    adjacent iff their difference is a non-zero multiple of a point of the hyperoval O = conic {(1,t,t^2)} +
    {(0,0,1)} + nucleus {(0,1,0)}. SRG(q^3, (q-1)(q+2), q-2, q+2); q = 4 gives SRG(64,18,2,6).
    '''
    p, n = prime_power(q)
    if p != 2 or n < 2:
        raise ValueError('hyperoval_gq needs q = 2^h, h >= 2')
    add, mul, neg, inv = _field(q)
    O = [(1, t, int(mul[t, t])) for t in range(q)] + [(0, 0, 1), (0, 1, 0)]
    conn = {tuple(int(mul[c, x]) for x in o) for o in O for c in range(1, q)}
    vecs = list(itertools.product(range(q), repeat=3))
    index = {v: i for i, v in enumerate(vecs)}
    A = np.zeros((len(vecs), len(vecs)), dtype=dtype)
    for v in vecs:
        for s in conn:
            A[index[v], index[tuple(int(add[a, b]) for a, b in zip(v, s))]] = 1
    return A


def hoffman_singleton() -> np.ndarray:
    '''the Hoffman-Singleton graph, SRG(50,7,0,1): five pentagons P_h, five pentagrams Q_i, and vertex j of
    P_h joined to vertex h*i + j (mod 5) of Q_i'''
    P = lambda h, j: 5 * h + j % 5
    Q = lambda i, j: 25 + 5 * i + j % 5
    A = np.zeros((50, 50), dtype=dtype)
    def edge(a, b):
        A[a, b] = A[b, a] = 1
    for h in range(5):
        for j in range(5):
            edge(P(h, j), P(h, j + 1))
            edge(Q(h, j), Q(h, j + 2))
            for i in range(5):
                edge(P(h, j), Q(i, h * i + j))
    return A


def _anisotropic_binary_form(q: int, add, mul):
    '''(a, b, c) with a x^2 + b x y + c y^2 != 0 for every (x, y) != (0, 0)'''
    for a, b, c in itertools.product(range(1, q), range(q), range(1, q)):
        if all(add[add[mul[a, mul[x, x]], mul[b, mul[x, y]]], mul[c, mul[y, y]]] != 0
               for x in range(q) for y in range(q) if (x, y) != (0, 0)):
            return a, b, c
    raise AssertionError('no anisotropic binary form found')


def affine_polar(q: int, m: int, elliptic: bool, nonisotropic: bool = False) -> np.ndarray:
    '''
    the affine polar graph VO(2m, q): vectors of GF(q)^(2m), x ~ y iff Q(x - y) = 0 (x != y) for a hyperbolic
    (elliptic) quadratic form Q = x0 x1 + ... [+ an anisotropic binary form in the last two coordinates].
    VO+(6,2) = SRG(64,35,18,20), VO-(6,2) = SRG(64,27,10,12), VO-(4,3) = SRG(81,20,1,6).
    With nonisotropic=True (odd q) x ~ y iff Q(x - y) is a non-zero square instead: VNO-(4,3) = SRG(81,30,9,12).
    '''
    add, mul, neg, inv = _field(q)
    n = 2 * m
    if elliptic:
        a, b, c = _anisotropic_binary_form(q, add, mul)
    vecs = np.array(list(itertools.product(range(q), repeat=n)))

    def Q(v):
        s = 0
        pairs = m - 1 if elliptic else m
        for i in range(pairs):
            s = add[s, mul[v[2 * i], v[2 * i + 1]]]
        if elliptic:
            x, y = v[n - 2], v[n - 1]
            s = add[s, add[add[mul[a, mul[x, x]], mul[b, mul[x, y]]], mul[c, mul[y, y]]]]
        return s

    # Q on every difference vector, through the field's subtraction
    index = {tuple(v): i for i, v in enumerate(vecs)}
    if nonisotropic:
        squares = {int(mul[x, x]) for x in range(1, q)}
        zero = {d for d in range(len(vecs)) if int(Q(vecs[d])) in squares}
    else:
        zero = {d for d in range(len(vecs)) if Q(vecs[d]) == 0 and d != index[tuple([0] * n)]}
    sing = {tuple(vecs[d]) for d in zero}
    A = np.zeros((len(vecs), len(vecs)), dtype=dtype)
    for i, x in enumerate(vecs):
        for s in sing:
            y = tuple(int(add[xi, si]) for xi, si in zip(x, s))  # x + s: the set of singular vectors is symmetric
            A[i, index[y]] = 1
    return A


def hermitian_u42() -> np.ndarray:
    '''the U(4,2) polar graph SRG(45,12,3,3): the 45 isotropic points of the Hermitian form sum x_i conj(y_i) on
    PG(3,4) (conj(x) = x^2), adjacent iff orthogonal'''
    add, mul, neg, inv = _field(4)
    pts = _projective_points(4, 4, mul, inv)
    conj = lambda x: int(mul[x, x])

    def h(x, y):
        s = 0
        for a, b in zip(x, y):
            s = add[s, mul[a, conj(b)]]
        return s

    iso = [p for p in pts if h(p, p) == 0]
    n = len(iso)
    A = np.zeros((n, n), dtype=dtype)
    for i in range(n):
        for j in range(i + 1, n):
            if h(iso[i], iso[j]) == 0:
                A[i, j] = A[j, i] = 1
    return A


def _pg24():
    '''(points, lines) of the projective plane PG(2,4): 21 points and 21 lines of 5 points each'''
    add, mul, neg, inv = _field(4)
    pts = _projective_points(4, 3, mul, inv)
    index = {p: i for i, p in enumerate(pts)}
    lines = []
    for l in pts:  # the line orthogonal to l, as a set of point indices
        lines.append(frozenset(i for i, p in enumerate(pts)
                               if add[add[mul[l[0], p[0]], mul[l[1], p[1]]], mul[l[2], p[2]]] == 0))
    return pts, lines


def _hyperovals_pg24(lines) -> list:
    '''all 168 hyperovals (6 points, no three collinear) of PG(2,4), as frozensets of point indices'''
    through = {}
    for l in lines:
        for a in l:
            for b in l:
                if a < b:
                    through[(a, b)] = l
    out = []

    def extend(chosen, banned):
        if len(chosen) == 6:
            out.append(frozenset(chosen))
            return
        for c in range(chosen[-1] + 1 if chosen else 0, 21):
            if c in banned:
                continue
            nb = set(banned)
            for a in chosen:
                nb |= through[(a, c)]
            extend(chosen + [c], nb)

    extend([], set())
    return out


def steiner_s3622() -> list:
    '''
    the Steiner system S(3,6,22) (every 3 of 22 points lie in exactly one of the 77 blocks of size 6): the 21
    lines of PG(2,4), each extended by a point at infinity (21), plus one of the three classes of 56 hyperovals
    (two hyperovals are in the same class iff they meet in an even number of points).
    '''
    pts, lines = _pg24()
    hyper = _hyperovals_pg24(lines)
    assert len(hyper) == 168
    cls = [h for h in hyper if len(h & hyper[0]) % 2 == 0]
    assert len(cls) == 56
    blocks = [frozenset(l | {21}) for l in lines] + cls
    seen = {}
    for b in blocks:
        for tri in itertools.combinations(sorted(b), 3):
            seen[tri] = seen.get(tri, 0) + 1
    assert len(seen) == 1540 and set(seen.values()) == {1}, 'not a Steiner system S(3,6,22)'
    return blocks


def _disjointness_graph(sets: list) -> np.ndarray:
    n = len(sets)
    A = np.zeros((n, n), dtype=dtype)
    for i in range(n):
        for j in range(i + 1, n):
            if not (sets[i] & sets[j]):
                A[i, j] = A[j, i] = 1
    return A


def gewirtz() -> np.ndarray:
    '''the Gewirtz (Sims-Gewirtz) graph SRG(56,10,0,2): the 56 hyperovals of one class, adjacent iff disjoint'''
    return _disjointness_graph(steiner_s3622()[21:])


def m22_graph() -> np.ndarray:
    '''the M22 graph SRG(77,16,0,4): the 77 blocks of S(3,6,22), adjacent iff disjoint'''
    return _disjointness_graph(steiner_s3622())


def higman_sims() -> np.ndarray:
    '''the Higman-Sims graph SRG(100,22,0,6): a vertex joined to the 22 points of S(3,6,22), each point to the
    blocks containing it, and blocks to the blocks they are disjoint from'''
    blocks = steiner_s3622()
    A = np.zeros((100, 100), dtype=dtype)
    def edge(a, b):
        A[a, b] = A[b, a] = 1
    for pnt in range(22):
        edge(0, 1 + pnt)
    for bi, b in enumerate(blocks):
        for pnt in b:
            edge(1 + pnt, 23 + bi)
        for bj in range(bi + 1, 77):
            if not (b & blocks[bj]):
                edge(23 + bi, 23 + bj)
    return A


def _difference_triples(n: int, avoid=()):
    '''t base triples {0, a, a+b} of Z_n whose differences (up to sign) cover 1..(n-1)/2 except `avoid`, once each'''
    need = [d for d in range(1, (n - 1) // 2 + 1) if d not in avoid]
    def ds(a, b):
        return {min(x % n, (-x) % n) for x in (a, b, a + b)}
    def search(left, found):
        if not left:
            return found
        first = left[0]
        for a in range(1, n):
            for b in range(1, n):
                s = {min(x % n, (-x) % n) for x in (a, b, a + b)}
                if len(s) == 3 and first in s and s <= set(left):
                    r = search([d for d in left if d not in s], found + [(a, a + b)])
                    if r is not None:
                        return r
        return None
    return search(need, [])


def steiner_triple_system(v: int) -> list:
    '''a cyclic Steiner triple system STS(v) on Z_v (v = 1 or 3 mod 6, v >= 13): its blocks, as sorted triples'''
    if v % 6 not in (1, 3) or v < 13:
        raise ValueError(f'no cyclic STS({v}) here: need v = 1 or 3 mod 6, v >= 13')
    blocks = set()
    short = v % 6 == 3
    triples = _difference_triples(v, avoid=(v // 3,) if short else ())
    assert triples is not None
    for a, b in triples:
        for s in range(v):
            blocks.add(tuple(sorted(((s) % v, (s + a) % v, (s + b) % v))))
    if short:
        for s in range(v // 3):
            blocks.add(tuple(sorted((s, s + v // 3, s + 2 * v // 3))))
    assert len(blocks) == v * (v - 1) // 6
    return sorted(blocks)


def block_graph(blocks: list) -> np.ndarray:
    '''blocks adjacent iff they meet (for a Steiner triple system on v points: SRG(v(v-1)/6, 3(v-3)/2, (v+3)/2, 9))'''
    sets = [set(b) for b in blocks]
    n = len(sets)
    A = np.zeros((n, n), dtype=dtype)
    for i in range(n):
        for j in range(i + 1, n):
            if sets[i] & sets[j]:
                A[i, j] = A[j, i] = 1
    return A


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


def _params(A: np.ndarray) -> tuple:
    return tuple(int(x) for x in SRGProperties.from_matrix(A).vklu)


def _is_srg_with(A: np.ndarray, want: tuple) -> bool:
    '''A really is an SRG with these parameters (the parameters are read off the first rows, so check the identity too)'''
    from .model import PartialSRG
    with np.errstate(all='ignore'):
        return _params(A) == want and PartialSRG(A).solved()


def _geometry_matches(v: int, k: int, l: int, u: int):
    '''generalized quadrangles, Hoffman-Singleton, the U(4,2) polar graph and affine polar graphs'''
    want = (v, k, l, u)
    for q in (2, 3, 4, 5, 7, 8, 9):  # the symplectic GQ(q, q)
        if want == ((q + 1) * (q * q + 1), q * (q + 1), q - 1, q + 1):
            yield f'collinearity graph of the symplectic generalized quadrangle W({q}) = GQ({q},{q})', symplectic_gq(q)
    for q in (4, 8):  # GQ(q-1, q+1) from a hyperoval
        if want == (q ** 3, (q - 1) * (q + 2), q - 2, q + 2):
            yield f'collinearity graph of GQ({q - 1},{q + 1}) = T2*(O) from a hyperoval of PG(2,{q})', hyperoval_gq(q)
    if want == (50, 7, 0, 1):
        yield 'Hoffman-Singleton graph', hoffman_singleton()
    if want == (45, 12, 3, 3):
        yield 'U(4,2) polar graph (Hermitian variety in PG(3,4))', hermitian_u42()
    if want == (56, 10, 0, 2):
        yield 'Gewirtz graph (56 hyperovals of PG(2,4), adjacent iff disjoint)', gewirtz()
    if want == (77, 16, 0, 4):
        yield 'M22 graph (blocks of S(3,6,22), adjacent iff disjoint)', m22_graph()
    if want == (100, 22, 0, 6):
        yield 'Higman-Sims graph', higman_sims()
    for q in (2, 3, 4, 5):  # affine polar graphs VO+-(2m, q); parameters checked on the graph itself
        for m in (2, 3, 4):
            if q ** (2 * m) != v or v > 1100:
                continue
            for elliptic in (True, False):
                eps = -1 if elliptic else 1
                if k == (q ** m - eps) * (q ** (m - 1) + eps):  # the VO degree; VNO has a different one
                    A = affine_polar(q, m, elliptic)
                    if _is_srg_with(A, want):
                        yield f'affine polar graph VO{"-" if elliptic else "+"}({2 * m},{q})', A
                if q % 2 == 1 and v <= 800:  # the non-isotropic variant VNO+-: x ~ y iff Q(x - y) is a non-zero square
                    A = affine_polar(q, m, elliptic, nonisotropic=True)
                    if _is_srg_with(A, want):
                        yield f'affine polar graph VNO{"-" if elliptic else "+"}({2 * m},{q})', A


def _steiner_matches(v: int, k: int, l: int, u: int):
    '''block graph of a Steiner triple system STS(n): SRG(n(n-1)/6, 3(n-3)/2, (n+3)/2, 9)'''
    n = (1 + (1 + 24 * v) ** 0.5) / 2
    if n == int(n) and int(n) >= 13 and int(n) % 6 in (1, 3):
        n = int(n)
        if (k, l, u) == (3 * (n - 3) // 2, (n + 3) // 2, 9):
            yield f'block graph of a cyclic Steiner triple system STS({n})', block_graph(steiner_triple_system(n))


GENERATORS = [_paley_matches, _triangular_matches, _lattice_matches, _geometry_matches, _steiner_matches]  # each: (v, k, l, u) -> iterator of (name, adjacency matrix)


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

