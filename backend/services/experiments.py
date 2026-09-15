"""Reproducible pilot-result collection from generated match artifacts."""
from __future__ import annotations
import json
from pathlib import Path

def collect_pilot_rows(data_dir: Path) -> list[dict]:
    rows=[]
    for match_file in data_dir.glob('*/match.json'):
        match=json.loads(match_file.read_text())
        tracking=match_file.parent/'live_tracking.json'
        if tracking.exists():
            info=json.loads(tracking.read_text())
            rows.append({'video':match['name'],'duration_sec':round(match['duration'],1),'source':info['source'],'mean_players':info['mean_players'],'ball_visibility':info['ball_visibility'],'control_frames':info['control_frames']})
    return rows
