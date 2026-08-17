# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Complete enumeration solver that constructs the adjacency matrix(es) of a strongly regular graph
(SRG) — equivalently, a two-distance set — given parameters `(v, k, l, u)`:
- `v`: number of vertices
- `k`: degree (each vertex has exactly `k` neighbors)
- `l` (lambda): number of common neighbors for two *adjacent* vertices
- `u` (mu): number of common neighbors for two *non-adjacent* vertices

## Commands

```bash
# install (editable, brings in numpy/pytest/networkx/matplotlib/cython)
pip install -e .

# solve for a specific SRG parameter set, prints all adjacency matrices found
python -m srg 13 6 2 3

# browse the precomputed solution database (srg/database/problem_*.py)
python -m srg.database              # list available (v,k,l,u) problems
python -m srg.database list 13 6 2 3
python -m srg.database draw 13 6 2 3   # renders PNGs via networkx/matplotlib

# run tests
./run_all_tests.sh                          # currently just tests/test_cospectral.py
python3 -m pytest -vs --durations=0 tests/  # full suite
python3 -m pytest tests/test_solver.py::test_solve -vs   # single test

# optional: compile the hot-path modules with Cython for speed
./cythonize.sh      # copies srg/*.py -> *.pyx and builds *.so in place
./uncythonize.sh     # removes the generated .so/.pyx/.c files, reverting to pure Python

# profile
./profile_performance.sh   # cProfile over experiment.py (not committed — write one to profile against)
```

There is no lint config in the repo; don't invent one.

## Architecture

The solver treats "extend a partial SRG adjacency matrix by one more row" as a constraint
satisfaction problem, and backtracks (via an explicit stack, not recursion) over the tree of
possible next rows.

**`srg/srg.py`** — core data model:
- `SRGProperties(v,k,l,u)`: parameter validation (`is_srg`), derives eigenvalues/multiplicities/
  determinant/complement from `(v,k,l,u)`, and can be reconstructed `from_matrix`.
- `PartialSRG`: wraps a partial (top `R` rows known, symmetric-so-far) adjacency matrix as a
  numpy `int8` array. `complement_matrix()` flips the known rows; `solved()` checks the full SRG
  identity `M@M - (l-u)*M == (k-u)*I + u*J` once `R == v`. `append_and_return_new` adds one
  completed row.
- `Question`: the linear system for "what can the next row look like" — built via
  `Question.from_matrix(partial_matrix)` from the constraints implied by the rows seen so far.
  Wraps `A @ x = b` plus per-column `bounds` and quota, and an `Answer` that tracks which
  positions in the new row are still unknown (`-1` sentinel) vs. resolved.
- `Answer`: tracks resolved/unresolved counts per equivalence class of columns (`quota`,
  `unknown_loc`) and `binarize()`s a fully-resolved answer back into a 0/1 row.

**`srg/solver.py`** — the actual search:
- `_seed(v,k,l,u)`: builds the canonical first two rows to start from.
- `solve_question(Q)`: the propagate/branch loop. Each iteration runs a fixed-point of cheap
  deductions — `reduce_col` (merge duplicate columns via `unique._encode`), `eliminate`
  (Gaussian elimination over the `A@x=b` system, `gauss_elim.py`), `zero_in_b` (columns forced
  to 0 by tight bounds, `bounds.py`), `only_1_element_in_row` (rows that pin a single column) —
  until nothing changes, then either yields a solved row or branches via `fork_enum` (picks the
  column with the smallest bound and enumerates its feasible values, `fork.py`).
  All deduction steps are decorated with `@raiseExceptionIfNotSolvableAfterwards`, which raises
  `NoSolution` (caught in `solve_question`'s search loop to prune that branch) whenever bounds/
  quota become infeasible after a step. Steps are also `@debug`-decoratable (`utils.py`) to print
  before/after state and re-check invariants — commented out by default.
- `advance(partial)` / `solve(partial)`: drive the row-by-row construction: for each partial SRG,
  build its `Question`, enumerate all valid next rows via `solve_question`, append each to get new
  `PartialSRG`s, split into finished (`solved()`) vs. still-growing, and recurse until nothing is
  left to grow. `solve()` is a generator yielding completed adjacency matrices (numpy arrays).

**`srg/sorter.py`** — canonicalizes a solved matrix by permuting vertex labels to maximize its
binary encoding (`maximize`/`AdjMat.sort`), so isomorphic solutions compare equal; also sorts
lists of solution matrices into a canonical order (used to diff against the database in tests).

**`srg/database/`** — one `problem_V_K_L_U.py` module per known `(v,k,l,u)`, each exporting
`v,k,l,u,solutions` (a list of numpy adjacency matrices) as ground truth. `__init__.py` provides
`list_problems`, `extract_vklu`, `get_solutions`, and `draw` (renders via networkx/matplotlib).
Tests in `tests/test_database.py` and `tests/test_solver.py` are parametrized over every problem
in this directory, so adding a new verified `problem_*.py` module automatically extends coverage.

**Cython note:** every core module (`srg/*.py`, not `database/`) starts with `#!python` /
`#cython: language_level=3` shebang-style pragmas so `cythonize.sh` can copy them to `.pyx` and
compile in place for a speed boost; the modules are otherwise plain, pure-Python-compatible code
and run fine uninstalled/uncompiled.

## Gotchas

- `unique._encode(A)` (row-encodes columns, no `b`) and `gauss_elim._encode(A, b)` (also folds in
  `b`) are different functions with the same name in different modules — don't confuse them when
  navigating.
- `srg.dtype = np.int8` is used everywhere as an "ideal bool"; matrices should stay `int8`, not be
  upcast, since `unique`/`gauss_elim` bit-pack rows into integers keyed on column dtype width.
