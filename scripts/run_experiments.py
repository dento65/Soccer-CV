"""Rebuild decoder-sensitivity evidence from saved, named match artifacts.

Usage: PYTHONPATH=. .venv/bin/python scripts/run_experiments.py
This script never reruns neural inference. It records that saved proposal outputs
are reused, and sweeps only the project decoder implementation.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.engine import clips, interval_seconds
DATA = ROOT / 'data'
OUT = ROOT / 'evaluation'
TARGETS = {
    'supplied_calf': ('Training ground · supplied sample', 'SoccerNet CALF benchmark'),
    'video_motion': ('VIDEO.MP4', 'Frame-difference activity baseline'),
    'input_motion': ('INPUT_VID_30s.mp4', 'Frame-difference activity baseline'),
}
GRID = [(threshold, before, after) for threshold in (.05, .20, .40) for before, after in ((4, 3), (8, 5), (12, 8))]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    records, rows = [], []
    all_matches = []
    for match_path in DATA.glob('*/match.json'):
        match = json.loads(match_path.read_text())
        all_matches.append((match_path, match))
    selected = []
    for target, (name, source_prefix) in TARGETS.items():
        matches = [(path, match) for path, match in all_matches if match['name'] == name and match.get('events') and match.get('source', '').startswith(source_prefix)]
        if matches:
            selected.append((target, max(matches, key=lambda item: item[0].stat().st_mtime)))
    for target, (match_path, match) in selected:
        if not match.get('events'):
            continue
        video = match_path.parent / 'source.mp4'
        tracking_path = match_path.parent / 'live_tracking.json'
        tracking = json.loads(tracking_path.read_text()) if tracking_path.exists() else {}
        records.append({'target': target, 'match_id': match['id'], 'name': match['name'], 'duration_seconds': match['duration'], 'source_sha256': sha256(video), 'event_source': match['source'], 'proposal_count': len(match['events']), 'tracking': {key: tracking.get(key) for key in ('mean_players', 'ball_visibility', 'control_frames', 'frame_count')}, 'cache_status': 'saved model output reused for decoder sweep'})
        for threshold, before, after in GRID:
            output = clips(match['events'], match['duration'], threshold=threshold, before=before, after=after)
            raw = sum(max(0, min(match['duration'], event['timestamp_sec'] + after) - max(0, event['timestamp_sec'] - before)) for event in match['events'] if event['confidence'] >= threshold)
            union = interval_seconds([(clip['start_sec'], clip['end_sec']) for clip in output])
            rows.append({'target': target, 'match_id': match['id'], 'name': match['name'], 'threshold': threshold, 'before_seconds': before, 'after_seconds': after, 'policy': 'asymmetric', 'accepted_proposals': sum(len(clip['events']) for clip in output), 'clip_count': len(output), 'union_seconds': round(union, 3), 'raw_window_seconds': round(raw, 3), 'redundant_seconds_removed': round(raw - union, 3), 'context_metrics': 'unavailable: no independent human context annotations'})
    payload = {'schema': 'pitchclipers-decoder-sweep-v1', 'created_at_utc': datetime.now(timezone.utc).isoformat(), 'method': 'Saved model proposal outputs; decoder-only sensitivity sweep. No accuracy claim.', 'videos': records, 'rows': rows}
    (OUT / 'decoder_sweep.json').write_text(json.dumps(payload, indent=2))
    with (OUT / 'decoder_sweep.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ['match_id'])
        writer.writeheader(); writer.writerows(rows)
    print(f'Wrote {len(rows)} policy rows for {len(records)} saved videos to {OUT}')


if __name__ == '__main__':
    main()
