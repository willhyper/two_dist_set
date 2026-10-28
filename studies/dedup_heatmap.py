"""Render cumulative partial-key metrics as a standalone interactive heatmap.

Usage: python studies/dedup_heatmap.py HISTORY OUTPUT --quest 28 12 6 4
HISTORY is dedup_progress JSONL or a parallel solver stderr log.
"""
import argparse
import csv
import html
import io
import json
from pathlib import Path


def load_snapshots(path):
    snapshots = []
    with Path(path).open() as source:
        for line in source:
            if not line.endswith('\n'):
                continue  # a live writer may not have finished its last record
            payload = line.split('; dedup: ', 1)[-1].strip()
            try:
                record = json.loads(payload)
            except ValueError:
                continue
            if isinstance(record, dict) and 'by_rows' in record and 'elapsed_sec' in record:
                if snapshots and record['elapsed_sec'] < snapshots[-1]['elapsed_sec']:
                    raise ValueError('history contains a restarted run; use one run per file')
                snapshots.append(record)
    if not snapshots:
        raise ValueError('no deduplication snapshots found; older runs cannot be reconstructed')
    return snapshots


def render(source, output, quest):
    records = load_snapshots(source)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    csv_path = output.with_suffix('.csv')
    fields = ['elapsed_sec', 'state', 'rows', 'candidates', 'keys', 'duplicate_hits',
              'local_duplicate_hits', 'shared_duplicate_hits', 'canonicalization_skips',
              'payload_bytes', 'table_bytes']
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for record in records:
        for rows, counts in sorted(record['by_rows'].items(), key=lambda pair: int(pair[0])):
            writer.writerow(dict(elapsed_sec=record['elapsed_sec'], state=record['state'], rows=rows,
                                 **{name: counts[name] for name in fields[3:]}))
    csv_path.write_text(buffer.getvalue())
    title = 'SRG(' + ','.join(map(str, quest)) + ')'
    template = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__ deduplication</title>
<style>
body{font:15px system-ui;margin:24px;background:#f5f7fa;color:#182433}main{max-width:1400px;margin:auto}
h1{font-size:24px}p{line-height:1.5;color:#475569}.controls{display:flex;gap:18px;flex-wrap:wrap;align-items:center}
section{background:white;padding:18px;border-radius:12px;margin-top:18px}.layout{display:flex;gap:24px;flex-wrap:wrap}
.chart{flex:1;min-width:300px;overflow:auto}svg{width:100%;min-width:450px}table{border-collapse:collapse;font-variant-numeric:tabular-nums}
th,td{padding:6px 10px;text-align:right;border-bottom:1px solid #dde3eb}th:first-child,td:first-child{text-align:left}
tfoot{font-weight:bold}#details{overflow:auto}.legend{height:12px;width:220px;background:linear-gradient(90deg,#f0f6ff,#90c2e7,#2b75b8,#08306b)}
button,select{font:inherit;padding:5px}a{color:#2457b2}#status{font-weight:600}
</style><main><h1>__TITLE__: deduplication by rows built</h1>
<p>Counts accumulate since solve start. Choose a metric for the heatmap; select a snapshot to inspect its exact table.</p>
<section class="controls"><label>Colour <select id="metric"><option value="duplicate_hits">Duplicate hits</option><option value="keys">Retained canonical keys</option><option value="candidates">Candidates reaching deduplication</option><option value="payload_bytes">Key payload bytes</option><option value="table_bytes">Allocated table bytes</option></select></label>
<label>Snapshot <input type="range" id="snapshot" min="0" max="__LAST__" value="__LAST__"></label>
<a href="__CSV__" download>Download table history CSV</a></section>
<section><div id="status"></div><div class="layout"><div class="chart"><svg id="plot" role="img" aria-label="Cumulative deduplication counts by row depth and elapsed time"></svg><div class="legend"></div><p id="scale"></p></div><div id="details"></div></div></section>
<p>Duplicate hits count rejected candidates once, combining local and shared lookups. Candidates passed spectral/Gram checks.
Complete solutions and the initial seed are excluded. Missing row depths in a recorded snapshot have zero counts.</p>
<p>Local hit/skip counters arrive when worker slices return; live or capped snapshots can be incomplete.
Allocated bytes include empty slots and occupancy, excluding Python headers, worker sets and RSS.
A rejection percentage does not measure CPU saved. Unrecorded history is not backfilled.</p></main>
<script>
const DATA=__DATA__, ROWS=__ROWS__;
const metric=document.querySelector('#metric'),slider=document.querySelector('#snapshot');
const fmt=n=>Number(n||0).toLocaleString();
function draw(){
 const selected=Number(slider.value),d=DATA[selected],name=metric.value;
 const unit=DATA[DATA.length-1].elapsed_sec>=3600?3600:1,unitName=unit===3600?'hours':'seconds';
 const last=DATA[DATA.length-1].elapsed_sec/unit,end=last>0?last*1.03:1;
 const left=55,top=25,w=720,h=ROWS.length*23,bottom=65,pw=w-left-20;
 const x=t=>left+t/unit/end*pw;
 const values=DATA.flatMap(d=>ROWS.map(r=>(d.by_rows[r]||{})[name]||0)),max=Math.max(1,...values);
 const color=n=>{if(!n)return '#f5f7fa';const t=Math.log1p(n)/Math.log1p(max);return `rgb(${Math.round(240-232*t)},${Math.round(246-198*t)},${Math.round(255-148*t)})`;};
 let svg=`<rect width="${w}" height="${h+top+bottom}" fill="white"/>`;
 ROWS.forEach((r,ri)=>{const y=top+ri*23;svg+=`<text x="${left-9}" y="${y+16}" text-anchor="end" font-size="12">${r}</text>`;
 DATA.forEach((s,i)=>{const n=(s.by_rows[r]||{})[name]||0;
 // Each column is a recorded snapshot, with midpoint display boundaries.
 const a=i?x((DATA[i-1].elapsed_sec+s.elapsed_sec)/2):left;
 const b=i+1<DATA.length?x((s.elapsed_sec+DATA[i+1].elapsed_sec)/2):left+pw;
 svg+=`<rect data-index="${i}" x="${a}" y="${y}" width="${Math.max(.5,b-a)}" height="22" fill="${color(n)}" stroke="${i===selected?'#d97706':'white'}" stroke-width="${i===selected?1.4:.3}"><title>${s.elapsed_sec.toFixed(3)} seconds; ${r} rows; ${name}: ${n}</title></rect>`;
 if(DATA.length<=4&&b-a>35)svg+=`<text pointer-events="none" x="${(a+b)/2}" y="${y+16}" text-anchor="middle" font-size="12" fill="${n>0&&Math.log1p(n)/Math.log1p(max)>.55?'white':'#182433'}">${fmt(n)}</text>`;
 });});
 const ticks=[...new Set([0,...DATA.map(s=>s.elapsed_sec/unit),end])];
 const chosen=ticks.length<=7?ticks:Array.from({length:6},(_,i)=>end*i/5);
 chosen.forEach(t=>{svg+=`<text x="${left+t/end*pw}" y="${top+h+20}" text-anchor="middle" font-size="11">${t.toFixed(unit===3600?2:3)}</text>`;});
 svg+=`<text x="${left+pw/2}" y="${top+h+47}" text-anchor="middle" font-size="13">Elapsed solver time (${unitName})</text><text transform="translate(15 ${top+h/2}) rotate(-90)" text-anchor="middle" font-size="13">Rows built</text>`;
 const plot=document.querySelector('#plot');plot.setAttribute('viewBox',`0 0 ${w} ${top+h+bottom}`);plot.innerHTML=svg;
 plot.querySelectorAll('[data-index]').forEach(el=>el.addEventListener('click',()=>{slider.value=el.dataset.index;draw();}));
 let table='<table><thead><tr><th>Rows built</th><th>Candidates</th><th>New keys stored</th><th>Duplicate hits</th></tr></thead><tbody>';
 ROWS.forEach(r=>{const c=d.by_rows[r]||{};table+=`<tr><td>${r}</td><td>${fmt(c.candidates)}</td><td>${fmt(c.keys)}</td><td>${fmt(c.duplicate_hits)}</td></tr>`;});
 table+=`</tbody><tfoot><tr><td>Total</td><td>${fmt(d.candidates)}</td><td>${fmt(d.keys)}</td><td>${fmt(d.duplicate_hits)}</td></tr></tfoot></table>`;
 document.querySelector('#details').innerHTML=table;
 document.querySelector('#status').textContent=`${d.elapsed_sec.toFixed(3)} seconds · ${d.state} · ${fmt(d.keys)} retained keys · ${(100*d.duplicate_fraction).toFixed(1)}% duplicate rejections · local counters ${d.local_counts_complete?'complete':'incomplete'}`;
 document.querySelector('#scale').textContent=`Cumulative ${metric.options[metric.selectedIndex].text.toLowerCase()}; logarithmic colour scale, 0–${fmt(max)}. Orange outline: selected snapshot. Columns show recorded snapshots.`;
}
metric.addEventListener('change',draw);slider.addEventListener('input',draw);draw();
</script></html>'''
    # Escape script terminators in embedded JSON; the title is plain HTML text.
    data = json.dumps(records).replace('<', '\\u003c')
    rows = sorted({int(row) for record in records for row in record['by_rows']})
    page = (template.replace('__TITLE__', html.escape(title))
            .replace('__DATA__', data).replace('__ROWS__', json.dumps(rows))
            .replace('__LAST__', str(len(records)-1)).replace('__CSV__', html.escape(csv_path.name, quote=True)))
    output.write_text(page)
    return output, csv_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('history')
    parser.add_argument('output')
    parser.add_argument('--quest', type=int, nargs=4, required=True)
    args = parser.parse_args()
    for path in render(args.history, args.output, args.quest):
        print(path)
