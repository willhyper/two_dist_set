# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Complete enumeration solver that constructs the adjacency matrix(es) of a strongly regular graph
(SRG) — equivalently, a two-distance set — given parameters `(v, k, l, u)` (a "quest"):
- `v`: number of vertices
- `k`: degree (each vertex has exactly `k` neighbors)
- `l` (lambda): number of common neighbors for two *adjacent* vertices
- `u` (mu): number of common neighbors for two *non-adjacent* vertices

## Why this repo exists

The question being asked of a given quest `(v,k,l,u)` is fundamentally **existence**: does at
least one legitimate adjacency matrix satisfying these parameters exist? The solver answers this
by exhaustive backtracking search — it may produce zero matrices (proves no SRG exists for that
quest), a handful, or, for quests with a lot of symmetry, very many (some known solved quests have
on the order of `n!` matrices, once you count every vertex-relabeling of the same underlying
graph). **Once existence (or non-existence) is established, further enumeration has diminishing
value** — the working convention seen in the database today is to abort/cap around ~100 matrices
for a quest that's producing far more than that, rather than exhaust the full symmetry group.
(See `srg/database/problem_25_12_5_6.py` / `problem_26_10_3_4.py`'s docstrings — `"15!"` /
`"10!"` solutions, "too many, only list the first" — this is an established but currently
*manual* practice: nothing in `solver.py` or `srg/__main__.py` actually caps the search
automatically today. `srg/__main__.py`'s `sorter.sort(solver.solve(s))` fully drains the
`solve()` generator before it can return anything, since Python's `sorted()` requires a
materialized list — so a 100-cap can't currently be applied to the CLI's output even if you
wanted to, only by driving `solver.solve()` directly as a generator, e.g. with
`itertools.islice`. Worth fixing if this becomes a real bottleneck on a "many solutions" quest.)

**The single metric this repo optimizes for is wall-clock time to answer a quest** — how fast
can the solver reach "found N solutions" or "found none, search exhausted" for a given
`(v,k,l,u)`. Every algorithmic change to `solver.py`/`gauss_elim.py`/`bounds.py`/etc. should be
justified by making quests resolve faster, not by anything else.

Three concrete workflows built around that goal:
1. **Solve a quest, timed.** `python -m srg v k l u` (or driving `solver.solve()` directly, as
   `exp.py` does) runs the search and reports what it found. Timing a quest — especially a
   difficult one — is the whole point; `profile_performance.sh`/`exp.py` exist to make that
   repeatable and profileable.
2. **Bank solved quests as ground truth, permanently.** Once a quest is solved, its matrices get
   committed to `srg/database/problem_V_K_L_U.py` (see Architecture below) and are trusted from
   then on — **there is no reason to ever recompute a banked quest's solutions to re-verify
   correctness**; `tests/test_database.py` / `tests/test_solver.py` already lock that in via
   invariant checks (row sums, symmetry, eigenvalue/determinant identities, SRG-equation checks)
   run against the committed matrices, not against a fresh solve. The *only* legitimate reason to
   re-run a banked quest is to benchmark a new/faster algorithm against it — and when you do, the
   convention (see almost every `problem_*.py` docstring) is to **append** a new timing entry
   (hardware, Python version, optimization used, elapsed time) rather than replace the old ones,
   so the docstring reads as a running log of the quest getting faster over successive algorithm
   iterations. Real examples already in the database: `problem_21_10_4_5.py` (no solution: 71.05s
   → 23s multi-threaded → 20.77s multi-threaded+cythonized), `problem_21_10_5_4.py` (13.41s →
   11.97s cythonized → 4.773s multi-processed), `problem_28_12_6_4.py` (a single brutal
   `94904.01194787025 s` ≈ 26.4 hours — the kind of quest this repo's speedups matter most for).
   These logs are the closest thing this repo has to a benchmark suite: when evaluating whether an
   algorithm change actually helps, re-time a slow banked quest (ideally one that's *unsolved*,
   like `problem_21_10_4_5.py`'s SRG(21,10,4,5) — used as `exp.py`'s benchmark — since a
   no-solution quest can't take an early exit on finding an answer, so it forces the search to
   fully justify infeasibility) and compare against its logged history.
3. **Visualize a banked solution.** `python -m srg.database draw v k l u` renders a saved quest's
   matrices as graphs via networkx/matplotlib (`srg/database/__init__.py`'s `draw()`).

## Commands

```bash
# install (editable). Package lives under src/srg/ (src layout), so this is REQUIRED —
# unlike a flat layout, `python -m srg` / pytest / exp.py will NOT find the package by
# just running from the repo root without installing first:
pip install -e ".[test,viz]"     # test = pytest; viz = networkx+matplotlib, only needed
                                  # for srg.database.draw()

# solve for a specific SRG parameter set, prints all adjacency matrices found
python -m srg 13 6 2 3

# browse the precomputed solution database (srg/database/problem_*.py)
python -m srg.database              # list available (v,k,l,u) problems
python -m srg.database list 13 6 2 3
python -m srg.database draw 13 6 2 3   # renders PNGs via networkx/matplotlib

# run tests
./run_all_tests.sh                          # full suite (same as the line below)
python3 -m pytest -vs --durations=0 tests/  # `pytest` alone also works (testpaths in pyproject.toml)
python3 -m pytest tests/test_solver.py::test_solve -vs   # single test

# optional: compile the hot-path modules with Cython for speed. NOT part of the normal
# install/build — entirely opt-in, driven by these two scripts plus the minimal
# ext_modules-only setup.py (see the Cython note below).
./cythonize.sh      # copies src/srg/*.py -> *.pyx and builds *.so in place
./uncythonize.sh     # removes the generated .so/.pyx/.c files, reverting to pure Python

# profile / benchmark the solver
./profile_performance.sh   # cProfile -O over exp.py, which solves SRG(21,10,4,5) end to end
```

There is no lint config or CI in the repo; don't invent either without being asked.

## Architecture

The solver treats "extend a partial SRG adjacency matrix by one more row" as a constraint
satisfaction problem, and backtracks (via an explicit stack, not recursion) over the tree of
possible next rows.

The package lives at `src/srg/` (src layout). Module paths below are given relative to that
(e.g. "`srg/solver.py`" means `src/srg/solver.py`).

**`srg/model.py`** — core data model (deliberately not named `srg/srg.py` — that stutter was
renamed away; every import is `from .model import X` / `from srg.model import X`):
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
  `fork.enum(quota, bounds, loc)` only enumerates candidate values for *one* column (pruned by
  the sum of the other columns' bounds), leaving the rest to be pinned down by the next
  propagate/branch cycle. `srg/partition.py`'s `enum(s, bounds)` solves the more general problem —
  every full vector of the same length as `bounds` whose entries sum to `s` and are each
  `<= bounds[i]` — but nothing in the live solver calls it; it's currently unused, effectively a
  reference implementation of the bounded-partition enumeration `fork_enum` performs lazily one
  column at a time instead. Don't assume it's dead code to delete without checking first.
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

**`exp.py`** — the repo's scratch/experiment file, at repo root (not under `srg/` or `tests/`).
It's not a permanent module with a fixed contract — its content gets replaced whenever there's a
new experiment to run — but *currently* it solves `SRG(21,10,4,5)` (a known-no-solution instance,
`srg/database/problem_21_10_4_5.py`) end to end and asserts the result matches, making it double
as `profile_performance.sh`'s benchmark target. If you repurpose `exp.py` for a different
one-off investigation, `profile_performance.sh` will silently start profiling that instead —
check what's currently in `exp.py` before trusting a profiling number.

**Testing note:** `bounds.py`, `fork.py`, `gauss_elim.py`, and `unique.py` used to carry their own
`if __name__ == '__main__':` self-tests (only run via `python -m srg.<module>`, invisible to
`pytest`). Those have been ported into `tests/test_bounds.py` / `test_fork.py` /
`test_gauss_elim.py` / `test_unique.py` (plus a new `tests/test_partition.py` for the
previously-untested `partition.py`) — the modules themselves no longer have `__main__` blocks.
`srg/__main__.py` and `srg/database/__main__.py` are the only remaining `__main__` entry points,
and those are genuine CLIs (`python -m srg`, `python -m srg.database`), not self-tests.

**Cython note:** every core module (`srg/*.py`, not `database/`) starts with `#!python` /
`#cython: language_level=3` shebang-style pragmas so `cythonize.sh` can copy them to `.pyx` and
compile in place for a speed boost; the modules are otherwise plain, pure-Python-compatible code
and run fine uninstalled/uncompiled. This is entirely opt-in and decoupled from normal packaging:
`pyproject.toml` (the only thing `pip install` reads) declares a pure-Python build with no Cython
involvement at all. The root `setup.py` that still exists is a separate, minimal helper used only
by `cythonize.sh`'s `python setup.py build_ext --inplace` call — it carries no project metadata
(that all lives in `pyproject.toml`) and only ever contributes `ext_modules`, guarded so it's a
no-op (`ext_modules = []`) whenever no `.pyx` files exist yet. That guard is what fixes the bug
this used to have: the old `setup.py` called `cythonize("srg/*.pyx")` unconditionally, which
raised `ValueError: 'srg/*.pyx' doesn't match any files` and broke plain `pip install -e .`.

## Gotchas

- `unique._encode(A)` (row-encodes columns, no `b`) and `gauss_elim._encode(A, b)` (also folds in
  `b`) are different functions with the same name in different modules — don't confuse them when
  navigating.
- `model.dtype = np.int8` is used everywhere as an "ideal bool"; matrices should stay `int8`, not
  be upcast, since `unique`/`gauss_elim` bit-pack rows into integers keyed on column dtype width.
