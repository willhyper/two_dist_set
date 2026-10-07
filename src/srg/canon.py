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
        self.gens = []  # automorphisms found so far, as lists: image of each vertex
        self.run(color0, ())

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
            if self.best_cert is None or cert < self.best_cert:
                self.best_cert, self.best_order = cert, order
            elif cert == self.best_cert:
                g = [0] * n
                for a, b in zip(self.best_order, order):
                    g[a] = b
                self.gens.append(g)
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
            self.run(col2, prefix + (x,))
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


def _canonical(M: np.ndarray, leaf_budget: int):
    R, n, adj, color, wts = _build(M)

    def certificate(order):
        pos = [0] * n
        for p, x in enumerate(order):
            pos[x] = p
        # processed vertices come first in the order (colour 0 is the lowest)
        edges = tuple(sorted((min(pos[i], pos[j]), max(pos[i], pos[j]))
                             for i in range(R) for j in adj[i] if j > i))
        weights = tuple(wts[x - R] for x in order[R:])
        return (edges, weights)

    try:
        return _Search(adj, color, certificate, leaf_budget).best_cert
    except BudgetExceeded:
        return None


def canonical_key(M: np.ndarray, leaf_budget: int = LEAF_BUDGET):
    '''hashable key equal for isomorphic partial matrices (and only those),
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
    out = np.zeros((v, v), dtype=A.dtype)
    for i, j in cert[0]:
        out[i, j] = out[j, i] = 1
    return out
