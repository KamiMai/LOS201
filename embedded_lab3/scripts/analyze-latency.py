#!/usr/bin/env python3
"""Pool four cyclictest threads without losing histogram overflow counts."""
import json
from pathlib import Path

lab = Path(__file__).resolve().parent.parent
summary = {}
for mode in ('idle', 'loaded'):
    data = json.loads((lab / 'logs' / f'cyclic_{mode}.json').read_text())
    threads = list(data['thread'].values())
    total = sum(t['cycles'] for t in threads)
    hist = {}
    for thread in threads:
        for bucket, count in thread['histogram'].items():
            key = int(bucket)
            hist[key] = hist.get(key, 0) + count
    def percentile(q):
        seen = 0
        for bucket, count in sorted(hist.items()):
            seen += count
            if seen >= total * q: return bucket
        return None
    summary[mode] = {
        'start': data['start_time'], 'end': data['end_time'],
        'min_us': min(t['min'] for t in threads),
        'avg_us': sum(t['avg'] * t['cycles'] for t in threads) / total,
        'max_us': max(t['max'] for t in threads),
        'cycles': total, 'histogram_count': sum(hist.values()),
        'overflow_count': total - sum(hist.values()),
        'p50_us': percentile(.5), 'p95_us': percentile(.95), 'p99_us': percentile(.99),
        'below_50_percent': 100 * sum(c for b, c in hist.items() if b < 50) / total,
        'threads': [{k: v for k, v in t.items() if k != 'histogram'} for t in threads],
    }
    assert summary[mode]['overflow_count'] >= 0
(lab / 'logs' / 'latency_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
