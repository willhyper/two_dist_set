# srg

Complete enumeration solver for strongly regular graphs (SRGs), equivalently two-distance sets.
Given parameters `(v, k, l, u)` — vertex count, degree, and the two common-neighbor counts — it
answers whether at least one adjacency matrix satisfying those parameters exists, and if so,
constructs it (and any others, up to a cap — see below).

## Install

```bash
pip install -e ".[test,viz]"
```

`test` pulls in `pytest`; `viz` pulls in `networkx`/`matplotlib`, only needed for
`python -m srg.database draw`. Both are optional — `pip install -e .` alone is enough just to run
the solver.

## Usage

Solve a quest `(v, k, l, u)`, printing every adjacency matrix found:

```bash
python -m srg 13 6 2 3
```

The search stops after 100 solutions by default (highly symmetric quests can otherwise have
astronomically many isomorphic matrices) — pass a 5th argument to override that cap:

```bash
python -m srg 13 6 2 3 5     # stop after 5 solutions instead of 100
```

Browse or draw previously-solved quests, banked as ground truth under `srg/database/`:

```bash
python -m srg.database                    # list every solved (v,k,l,u) quest
python -m srg.database list 13 6 2 3      # print that quest's saved matrices
python -m srg.database draw 13 6 2 3      # render them as PNGs via networkx/matplotlib
```

## Tests

```bash
./run_all_tests.sh
```

See `CLAUDE.md` for the architecture and design intent behind the repo.
