# Rust canonicalization and Python interoperability

The `rust-canonical` feature branch ports the complete canonicalizer to Rust:
column-class construction, color refinement, individualization, automorphism
orbits, backjump pruning, leaf budgeting, and the exact packed certificate.
The existing Python implementation remains in `canon._canonical_python` as a
reference and fallback. `canonical_key`, `canonical_matrix`, and `decode_key`
keep their public interfaces and key encoding.

The native crate has no third-party dependencies. It builds a [C ABI shared
library](https://doc.rust-lang.org/nomicon/ffi.html), called by the standard
Python [`ctypes` library](https://docs.python.org/3.9/library/ctypes.html). Each call owns an input
snapshot and a Python-allocated output buffer; Rust allocations are freed before
return. The GIL is released during the native call. No Python objects, callbacks,
or CPython ABI symbols cross the boundary. Native panics become an explicit
error status rather than unwinding into Python. Budget exhaustion still returns
`None`; invalid inputs or native failures are errors, never duplicate rejections.

## Build and select a backend

In a source checkout or editable install, using Rust 1.70+:

```bash
python -m pip install -e '.[test]'
python build_rust.py
python -c 'from srg import canon; print(canon.CANON_BACKEND)'
```

`build_rust.py` builds in release mode with the locked, dependency-free Cargo
manifest and atomically copies the host library into `src/srg`. It finds Cargo
on PATH or in `~/.cargo/bin`. Compile on each target OS/architecture. Binaries
are ignored by Git. Normal Python installations remain pure Python; this helper
is for source/editable installs, not a native wheel publishing workflow.

`SRG_CANON_BACKEND=auto` (default) selects Rust when a built library is present,
otherwise Python. `SRG_CANON_BACKEND=python` forces the reference backend.
`SRG_CANON_BACKEND=rust` requires the native library and fails clearly if absent.
An existing but incompatible library is an error; it is not silently ignored.
The backend is selected when `srg.canon` is imported, including spawned workers.
Restart Python after building. Building this isolated worktree does not change
an already running solver or the source tree it imported.

```bash
cargo test --locked --manifest-path rust/canon/Cargo.toml
cargo clippy --locked --manifest-path rust/canon/Cargo.toml --all-targets -- -D warnings
SRG_CANON_BACKEND=rust python -m pytest -q
SRG_CANON_BACKEND=python python -m pytest -q
```

## Exactness and measurement

Differential tests require identical full certificate bytes and identical
budget-exhaustion outcomes. They cover all banked graph prefixes, relabelings,
random symmetric partial matrices with tight budgets, NumPy layouts/dtypes,
concurrent calls, explicit backend selection, and invalid native inputs. The
full solver suite also runs through the Rust dispatcher.

`studies/compare_canon_backends.py` compares all 29 benchmark quests, alternating
which backend runs first with the same Python, source, worker count, hash seed,
and BLAS thread limits. Every returned solution must pass `PartialSRG.solved()`;
full certificates from the independent Python reference must match the complete
database set, with no duplicate solutions, before timing comparisons are used.
It records solver CPU and sampled process-tree RSS separately. RSS can count
shared pages multiple times. One paired pass under concurrent system load is
not a statistical estimate of speedup.

`studies/bench_canonical_calls.py` separately measures key computation including
Python buffer conversion and FFI overhead on actual generated feasible
SRG(36,14,4,6) candidates plus all prefixes of the six banked graphs. It checks
all keys before timing and alternates backends across repeated CPU measurements.
Neither benchmark attaches to, restarts, or modifies the ongoing full quest.

## Recorded results

Results are in `studies/results/rust_canonical_20261030/`, including the paired
CSV, per-quest exact certificates, measurement metadata, and repeated key-call
timings. The ongoing SRG(36,14,4,6) run used the existing Python code throughout.

| Measurement | Python | Rust |
| --- | ---: | ---: |
| Key-call median CPU, 1,559 calls | 1.109724 s | 0.133193 s |
| Median CPU per key, including interop | 711.82 microseconds | 85.43 microseconds |
| Total CPU across 29 quests, 4 workers | 931.605706 s | 880.178483 s |
| Highest sampled combined RSS | 178.56 MiB | 180.75 MiB |

Key computation was 8.33 times faster on the measured corpus. Whole-solver CPU
was 5.52% lower in the paired pass; memory did not improve. All 29 quests matched
the exact complete database sets (54 solutions per backend, including empty
sets for infeasible quests). This single paired pass shared the machine with
the ongoing long quest and other verification; CPU measurements do not remove
all effects of system load or process scheduling.

Validation: Rust unit tests (3 passed), strict Clippy and rustfmt checks; native
full suite (2,700 passed, 7 skipped, 1 xfailed); Python-forced full suite
(2,680 passed, 27 skipped, 1 xfailed, including 20 native-only skips). A normal
pure-Python wheel was built and checked without a native library. The same
shared library was also exercised with Python 3.9 and Python 3.15.
