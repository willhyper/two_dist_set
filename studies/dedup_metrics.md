# Partial-matrix deduplication metrics

The `dedup-metrics` branch records shared canonical-key storage and duplicate
rejections in `parallel.solve_parallel`. Search decisions and key encoding are
unchanged. Distinct raw labelings of isomorphic partial matrices already share
one exact canonical key, scoped to the number of rows built within one quest.
Full byte equality decides membership, even when hash values collide.

Ordinary parallel CLI/build progress lines now end with `; dedup: {JSON}`.
Redirect stderr to retain the complete history, including the final snapshot
before the manager process shuts down. No key contents are copied to the log.
Single-worker CLI runs use the serial solver and do not have these metrics.

For structured history, pass `dedup_progress` to `solve_parallel`:

```python
import json
from srg import parallel, solver
from srg.model import PartialSRG

# Put multiprocessing entry points under this guard on macOS/spawn.
if __name__ == '__main__':
    with open('dedup_history.jsonl', 'a') as history:
        def record(snapshot):
            history.write(json.dumps(snapshot) + '\n')
            history.flush()

        solutions = list(parallel.solve_parallel(
            PartialSRG(solver._seed(21, 10, 5, 4)),
            max_solutions=None, workers=2, dedup_progress=record))
```

Snapshots are emitted at startup, every progress interval (normally 5 seconds),
and at completion/cap. They contain:

| Field | Meaning |
| --- | --- |
| `keys` | Unique canonical partial keys retained in the shared store |
| `payload_bytes` | Sum of their complete encoded key lengths |
| `table_bytes` | Allocated packed slots: key space, occupancy bytes, unused capacity |
| `local_duplicate_hits` | Rejections by worker-local sets, batched once per slice |
| `shared_duplicate_hits` | Rejections by the manager store after local lookup misses |
| `duplicate_hits` | Sum of the two rejection counts; each rejected candidate counts once |
| `canonicalization_skips` | Feasible candidates with no key because canonicalization exceeded its budget; search continues |
| `candidates` | Keys inserted + duplicate hits + canonicalization skips |
| `duplicate_fraction` | Duplicate hits / candidates (zero with no candidates) |
| `by_rows` | The same counts and storage bytes, grouped by rows built |
| `by_key_size` | Keys, storage bytes, and shared hits grouped by rows built and encoded key length |
| `elapsed_sec`, `state` | Time since solve start, and started/running/finished/stopped state |
| `local_counts_complete` | All worker slices returned; local counters are complete |

Each hit increments a counter; repeated hits against the same canonical key are
all counted. We retain aggregate counters rather than per-hit records or a
Python object per key. This keeps instrumentation storage proportional to the
number of row/length groups rather than to the number of duplicates.

Live local counters lag until the worker finishes its slice. Shared claims are
counted immediately. A capped/interrupted run may lose unreported local counts;
`local_counts_complete` is false on a capped run with outstanding tasks. A normal
exhaustive final snapshot has complete counts. No shared snapshots are emitted
when `share_seen=False` or `isomorph_free=False`.

Metrics cover partial candidates that pass spectral/Gram checks. They exclude
spectrally rejected candidates, resumed roots, complete-solution deduplication,
and worker-local set memory. `table_bytes` excludes Python headers, temporary
resize buffers, and RSS. Key count/payload/retained slot bytes never decrease
within a solve; RSS need not follow them.

The rejection fraction measures how often deduplication prevents enqueuing a
partial candidate. It does not measure CPU saved or the number of descendant
expansions avoided: rejected subtrees can have very different sizes. Compare
solver CPU and exact canonical solution sets separately when evaluating speed.

## Smoke measurements (2026-10-27)

Both exhaustive runs used Python 3.9.6, two workers and 0.1-second slices. Every
returned matrix passed `PartialSRG.solved()` and each complete canonical solution
set exactly matched the database. These are instrumentation examples, not paired
speed benchmarks; scheduling can change the local/shared split and hit counts.

| Quest | Solutions | Retained keys | Key payload bytes | Allocated slot bytes | Local hits | Shared hits | Rejected / candidates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SRG(21,10,5,4) | 1 | 50 | 711 | 3,976 | 74 | 0 | 74 / 124 (59.7%) |
| SRG(28,12,6,4) | 4 | 227 | 6,466 | 18,104 | 251 | 14 | 265 / 492 (53.9%) |

Neither run encountered a canonicalization skip. Both final snapshots had
`local_counts_complete=true`.

## Interactive heatmap and row table

Render either the structured JSONL history above or a parallel solver stderr log:

```bash
python studies/dedup_heatmap.py dedup_history.jsonl dedup_heatmap.html --quest 28 12 6 4
```

The standalone HTML contains a selectable heatmap metric (duplicate hits,
retained keys, candidates, payload bytes, or allocated slot bytes) and the exact
per-row candidate/key/hit table for a selected snapshot. Click a heatmap column
or use the snapshot slider to update the table. The adjacent CSV exports every
recorded row/snapshot. All metrics use the same elapsed time coordinate; short
runs display seconds, longer runs hours. Values are cumulative, unlike the
pending-queue heatmap. Columns represent recorded snapshots, with midpoint
boundaries; they are not interpolated counts or hourly backfills.

The renderer does not modify the source history or any cron configuration.
Earlier runs without deduplication snapshots cannot supply this heatmap. It
ignores an unfinished last log line and refuses to combine restarted runs whose
elapsed time decreases.

## Standard quest report

Use one phone-readable figure with five stacked panels on the same elapsed-time
axis: (1) cumulative solution harvests, (2) pending partial matrices by rows
built, (3) duplicate hits added between adjacent hourly measurements by rows built,
(4) retained canonical keys by rows built, and (5) combined solver-process-tree RSS. The three distributions
are heatmaps; zero and unavailable observations must remain distinguishable.
Retained-key counts are cumulative. Duplicate-hit heatmap cells are differences
between adjacent hourly cumulative counters, not running totals; missing
intervals remain unavailable. Pending counts describe the parent queue at a snapshot. Keep local/shared hit definitions and RSS caveats
from above. Provide totals and links to the underlying measurements alongside
the figure, without a per-row text table.

For the full SRG(36,14,4,6) run requested on 2026-10-28, take hourly measurements
and deliver reports every four elapsed hours, plus a terminal report. There is
no runtime limit. The prior one-hour observation is a separate run; its saved
solutions remain banked, but its search stack was not persisted. Runtime logs,
monitoring scripts, and cron configuration live outside the repository.
