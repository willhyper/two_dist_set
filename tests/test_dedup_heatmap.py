"""Offline heatmaps must preserve measured row totals and reject mixed runs."""
import csv
import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('dedup_heatmap', Path(__file__).parents[1] / 'studies/dedup_heatmap.py')
heatmap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(heatmap)


def snapshot(elapsed):
    return dict(elapsed_sec=elapsed, state='finished', local_counts_complete=True,
                candidates=102, keys=24, duplicate_hits=78, duplicate_fraction=78/102,
                by_rows={'4': dict(candidates=102, keys=24, duplicate_hits=78,
                                  local_duplicate_hits=67, shared_duplicate_hits=11,
                                  canonicalization_skips=0, payload_bytes=241, table_bytes=688)})


def test_log_and_jsonl_export_same_measured_table(tmp_path):
    record = snapshot(42)
    source = tmp_path/'quest.err'
    source.write_text('unrelated log line\n[srg] finished; dedup: '+json.dumps(record)+'\n'
                      +json.dumps(snapshot(99)))  # incomplete tail is ignored
    assert heatmap.load_snapshots(source) == [record]
    page, table = heatmap.render(source, tmp_path/'chart.html', (28,12,6,4))
    with table.open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]['rows'] == '4'
    assert rows[0]['candidates'] == '102'
    assert rows[0]['keys'] == '24'
    assert rows[0]['duplicate_hits'] == '78'
    content = page.read_text()
    assert 'SRG(28,12,6,4)' in content
    assert '__DATA__' not in content
    assert '"candidates": 102' in content
    assert 'New keys stored' in content
    assert 'chart.csv' in content


def test_missing_metrics_cannot_be_reconstructed(tmp_path):
    source = tmp_path/'quest.err'
    source.write_text('finished: explored 100 partial matrices, 4 solutions\n')
    with pytest.raises(ValueError, match='cannot be reconstructed'):
        heatmap.load_snapshots(source)


def test_restarted_run_must_not_mix_cumulative_counters(tmp_path):
    source = tmp_path/'history.jsonl'
    source.write_text(''.join(json.dumps(snapshot(t))+'\n' for t in [42,3]))
    with pytest.raises(ValueError, match='restarted run'):
        heatmap.load_snapshots(source)
