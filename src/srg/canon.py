#!python
#cython: language_level=3
'''
Exact canonical form of a partial (or complete) SRG matrix, used for isomorph
rejection and for standardizing a solved matrix.

A partial matrix M (R rows x v columns, first R columns symmetric) is the
graph on the R "built" vertices plus, for every not-yet-built vertex, the set
of built vertices it is adjacent to (its column). Two partial matrices that
differ only by a relabeling of the built vertices and of the not-yet-built
vertices have exactly the same set of completions (up to isomorphism), so only
one of them needs to be searched.

Not-yet-built vertices with identical columns are interchangeable, so they are
collapsed into one weighted node. The resulting small graph is canonically
labeled by colour refinement + individualization search (a small nauty-style
search that prunes branches related by automorphisms already found). The
certificate is the full relabeled structure, so equal keys <=> isomorphic.
For a complete matrix (R == v) there are no unbuilt vertices and the key is
the canonical adjacency matrix itself - see canonical_matrix().
'''
import numpy as np

# Past this many leaves we give up on canonizing a matrix (it just won't be
# deduplicated) rather than risk an exponential blow-up on a pathological one.
LEAF_BUDGET = 5000


class BudgetExceeded(Exception): pass


class _Backjump(Exception):
    '''a leaf was found to be an automorphic image of an earlier leaf: return to the node at `depth`'''
    def __init__(self, depth: int):
        self.depth = depth


def _common_prefix(a: tuple, b: tuple) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def _refine(adj: list, color: list) -> list:
    '''1-WL colour refinement. Colours are ranks of label-independent
    signatures, so the result does not depend on the input vertex order.'''
    n = len(color)
    while True:
        sig = [(color[i], tuple(sorted([color[j] for j in adj[i]]))) for i in range(n)]
        ranks = {s: r for r, s in enumerate(sorted(set(sig)))}
        new = [ranks[s] for s in sig]
        if len(ranks) == len(set(color)):
            return new
        color = new


class _Search:
    def __init__(self, adj, color0, certificate, leaf_budget):
        self.adj, self.certificate = adj, certificate
        self.n = len(color0)
        self.budget = leaf_budget
        self.best_cert = None
        self.best_order = None
        self.first_cert = None  # the first leaf reached: leaves equal to it are automorphic images of it
        self.first_order = None
        self.first_path = None  # the individualized vertices leading to it (likewise for the best leaf)
        self.best_path = None
        self.gens = []  # automorphisms found so far, as lists: image of each vertex
        self.run(color0, ())

    def _automorphism(self, order_a, order_b):
        '''two leaves with the same certificate: the map order_a[i] -> order_b[i] is an automorphism'''
        g = [0] * self.n
        for a, b in zip(order_a, order_b):
            g[a] = b
        self.gens.append(g)

    def _orbit_rep(self, prefix, cell):
        '''partition cell into orbits of the automorphisms fixing prefix pointwise'''
        fixed = [g for g in self.gens if all(g[x] == x for x in prefix)]
        parent = {x: x for x in cell}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        members = set(cell)
        for g in fixed:
            for x in cell:
                y = g[x]
                if y in members:
                    parent[find(x)] = find(y)
        return find

    def run(self, color, prefix):
        color = _refine(self.adj, color)
        n = self.n

        cells = {}
        for i, c in enumerate(color):
            cells.setdefault(c, []).append(i)
        target = None
        for c in sorted(cells):
            cell = cells[c]
            if len(cell) > 1 and (target is None or len(cell) < len(target[1])):
                target = (c, cell)

        if target is None:  # discrete: a leaf
            self.budget -= 1
            if self.budget < 0:
                raise BudgetExceeded
            order = sorted(range(n), key=color.__getitem__)
            cert = self.certificate(order)
            if self.first_cert is None:
                self.first_cert, self.first_order, self.first_path = cert, order, prefix
            elif cert == self.first_cert:
                self._automorphism(self.first_order, order)
                raise _Backjump(_common_prefix(prefix, self.first_path))
            if self.best_cert is None or cert < self.best_cert:
                self.best_cert, self.best_order, self.best_path = cert, order, prefix
            elif cert == self.best_cert:
                self._automorphism(self.best_order, order)
                raise _Backjump(_common_prefix(prefix, self.best_path))
            return

        c, cell = target
        tried = []
        for x in cell:
            if tried and self.gens:
                find = self._orbit_rep(prefix, cell)
                if any(find(x) == find(t) for t in tried):
                    continue
            # individualize x: it gets a colour strictly below the rest of its cell
            col2 = [2 * ci + (1 if (ci == c and i != x) else 0) for i, ci in enumerate(color)]
            try:
                self.run(col2, prefix + (x,))
            except _Backjump as jump:
                if jump.depth != len(prefix):
                    raise  # the divergence point is further up
                # this child's subtree is the image of one that was already explored: go on to the next child
            tried.append(x)


def _build(M: np.ndarray):
    R, v = M.shape
    rest = M[:, R:]
    if rest.shape[1]:
        cols, counts = np.unique(rest, axis=1, return_counts=True)
        cols = cols.T  # (m, R)
        counts = counts.tolist()
    else:
        cols, counts = np.zeros((0, R), dtype=M.dtype), []
    m = len(counts)
    n = R + m

    block = M[:, :R].tolist()
    colsl = cols.tolist()

    adj = [[] for _ in range(n)]
    for i in range(R):
        row = block[i]
        for j in range(R):
            if row[j]:
                adj[i].append(j)
    for c in range(m):
        cv = colsl[c]
        for i in range(R):
            if cv[i]:
                adj[i].append(R + c)
                adj[R + c].append(i)

    # processed vertices share one colour; class nodes are coloured by weight
    color = [0] * R + [1 + w for w in counts]
    return R, n, adj, color, counts


_TRIU = {}


def _triu(n: int):
    if n not in _TRIU:
        _TRIU[n] = np.triu_indices(n, 1)
    return _TRIU[n]


def _canonical(M: np.ndarray, leaf_budget: int):
    R, n, adj, color, wts = _build(M)

    A = np.zeros((n, n), dtype=np.uint8)
    for i, nbrs in enumerate(adj):
        A[i, nbrs] = 1
    iu = _triu(n)
    wts_arr = np.array(wts, dtype=np.uint8)

    def certificate(order):
        # processed vertices come first in the order (colour 0 is the lowest)
        o = np.array(order)
        bits = np.packbits(A[np.ix_(o, o)][iu])
        return bits.tobytes() + wts_arr[o[R:] - R].tobytes()

    try:
        return _Search(adj, color, certificate, leaf_budget).best_cert
    except BudgetExceeded:
        return None


def canonical_key(M: np.ndarray, leaf_budget: int = LEAF_BUDGET):
    '''compact bytes key, equal for isomorphic partial matrices (and only those),
    or None if the matrix is too symmetric to canonize within leaf_budget.'''
    return _canonical(M, leaf_budget)


def canonical_matrix(A: np.ndarray, leaf_budget: int = 10 ** 7) -> np.ndarray:
    '''
    the standard form of a complete adjacency matrix: isomorphic graphs map to
    the identical matrix, and non-isomorphic graphs to different ones.
    '''
    R, v = A.shape
    assert R == v, 'canonical_matrix needs a complete (square) matrix'
    cert = _canonical(A, leaf_budget)
    assert cert is not None, 'leaf budget exceeded'
    nbits = v * (v - 1) // 2
    bits = np.unpackbits(np.frombuffer(cert[:(nbits + 7) // 8], dtype=np.uint8))[:nbits]
    out = np.zeros((v, v), dtype=A.dtype)
    out[_triu(v)] = bits
    return out + out.T
