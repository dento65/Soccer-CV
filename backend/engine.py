"""Detector-independent highlight decoding and context evaluation in seconds.

The policies operate on model proposals. Confidence is an action-spotter score, not
a calibrated probability or an estimate of perceived highlight quality.
"""
from __future__ import annotations

import math
import numpy as np

CLASSES = ['activity','goal','penalty','shot','foul','yellow_card','red_card','corner','offside','substitution','free_kick']
ALIASES = {'shots on target':'shot','shots off target':'shot','yellow card':'yellow_card','red card':'red_card','yellow->red card':'red_card','direct free-kick':'free_kick','indirect free-kick':'free_kick'}


def normalize(payload, duration, half=1):
    rows = payload if isinstance(payload, list) else payload.get('predictions', payload.get('events', []))
    if not isinstance(rows, list) or len(rows) > 100000:
        raise ValueError('Expected a list of at most 100,000 events')
    result = []
    for i, row in enumerate(rows):
        if int(row.get('half', half)) != half:
            continue
        label = str(row.get('class_id', row.get('label', 'activity'))).lower()
        label = ALIASES.get(label, label.replace(' ', '_'))
        timestamp = float(row['timestamp_sec']) if 'timestamp_sec' in row else float(row['position']) / 1000
        confidence = float(row.get('confidence', row.get('score', 1)))
        if not math.isfinite(timestamp + confidence) or not 0 <= timestamp <= duration or not 0 <= confidence <= 1:
            raise ValueError(f'Invalid event {i}: timestamp/score outside range')
        result.append({'event_id': str(row.get('event_id', f'e{i}')), 'class_id': label, 'timestamp_sec': timestamp, 'confidence': confidence})
    return sorted(result, key=lambda row: (row['timestamp_sec'], row['event_id']))


def _interval(event, duration, before, after):
    return max(0.0, float(event['timestamp_sec']) - before), min(float(duration), float(event['timestamp_sec']) + after)


def union(intervals):
    """Validated union. Touching windows are deliberately merged."""
    output = []
    for start, end in sorted((float(a), float(b)) for a, b in intervals):
        if not math.isfinite(start + end) or end < start:
            raise ValueError('Intervals must have finite ordered bounds')
        if end == start:
            continue
        if output and start <= output[-1][1]:
            output[-1][1] = max(output[-1][1], end)
        else:
            output.append([start, end])
    return output


def interval_seconds(intervals):
    return sum(end - start for start, end in union(intervals))


def _make_clip(index, start, end, events, reason):
    ordered = sorted(events, key=lambda row: (row['timestamp_sec'], row['event_id']))
    labels = list(dict.fromkeys(event['class_id'] for event in ordered))
    return {'clip_id': f'c{index}', 'start_sec': round(start, 4), 'end_sec': round(end, 4),
            'duration_sec': round(end - start, 4), 'label': ' + '.join(labels), 'events': ordered,
            'event_ids': [event['event_id'] for event in ordered], 'selection_reason': reason}


def fixed_windows(events, duration, threshold=.5, before=8, after=5, classes=None, thresholds=None):
    """Confidence-filtered asymmetric windows merged by overlap."""
    accepted = []
    for event in sorted(events, key=lambda row: (row['timestamp_sec'], row['event_id'])):
        if classes is not None and event['class_id'] not in classes:
            continue
        if event['confidence'] < (thresholds or {}).get(event['class_id'], threshold):
            continue
        start, end = _interval(event, duration, before, after)
        if end > start:
            accepted.append((start, end, event))
    output = []
    for start, end, event in accepted:
        if output and start <= output[-1]['end_sec']:
            output[-1]['end_sec'] = max(end, output[-1]['end_sec'])
            output[-1]['events'].append(event)
        else:
            output.append({'start_sec': start, 'end_sec': end, 'events': [event]})
    return [_make_clip(index, row['start_sec'], row['end_sec'], row['events'], 'confidence threshold; overlapping windows merged') for index, row in enumerate(output)]


def budgeted_windows(events, duration, budget_seconds, threshold=.5, before=8, after=5, classes=None, thresholds=None):
    """Greedy score-per-added-second selection under a union-duration budget.

    It is a deterministic proxy policy, not an optimizer of human enjoyment.
    """
    if not math.isfinite(float(budget_seconds)) or float(budget_seconds) <= 0:
        raise ValueError('budget_seconds must be positive')
    candidates = []
    for event in events:
        if classes is not None and event['class_id'] not in classes:
            continue
        if event['confidence'] < (thresholds or {}).get(event['class_id'], threshold):
            continue
        start, end = _interval(event, duration, before, after)
        if end > start:
            candidates.append((start, end, event))
    selected, current = [], []
    while candidates:
        scored = []
        for start, end, event in candidates:
            added = interval_seconds(current + [(start, end)]) - interval_seconds(current)
            utility = float(event['confidence']) * 1_000_000 if added <= 1e-9 else float(event['confidence']) / added
            scored.append((utility, event['confidence'], -event['timestamp_sec'], str(event['event_id']), start, end, event))
        _, _, _, _, start, end, event = max(scored)
        candidates = [row for row in candidates if row[2]['event_id'] != event['event_id']]
        if interval_seconds(current + [(start, end)]) <= float(budget_seconds) + 1e-9:
            current.append((start, end))
            selected.append((start, end, event))
    merged = []
    for start, end, event in sorted(selected, key=lambda row: (row[0], row[2]['event_id'])):
        if merged and start <= merged[-1]['end_sec']:
            merged[-1]['end_sec'] = max(merged[-1]['end_sec'], end)
            merged[-1]['events'].append(event)
        else:
            merged.append({'start_sec': start, 'end_sec': end, 'events': [event]})
    return [_make_clip(index, row['start_sec'], row['end_sec'], row['events'], f'greedy score-per-added-second under {float(budget_seconds):g}s union budget') for index, row in enumerate(merged)]


def clips(events, duration, threshold=.5, before=8, after=5, classes=None, thresholds=None, policy='asymmetric', budget_seconds=None):
    if policy == 'symmetric':
        after = before
    if policy == 'budget':
        return budgeted_windows(events, duration, budget_seconds, threshold, before, after, classes, thresholds)
    if policy not in {'asymmetric', 'symmetric'}:
        raise ValueError('policy must be asymmetric, symmetric, or budget')
    return fixed_windows(events, duration, threshold, before, after, classes, thresholds)


def _validate_intervals(rows, duration, kind):
    values = []
    for index, row in enumerate(rows):
        start, end = float(row['start_sec']), float(row['end_sec'])
        if not math.isfinite(start + end) or not 0 <= start < end <= duration:
            raise ValueError(f'{kind} interval {index} must be finite, ordered, and inside video duration')
        values.append((start, end))
    return values


def _overlap_length(first, second):
    return sum(max(0, min(a_end, b_end) - max(a_start, b_start)) for a_start, a_end in first for b_start, b_end in second)


def evaluate(selected, references, duration):
    """Project-defined evaluation against independent human context intervals."""
    refs = _validate_intervals(references, duration, 'Reference')
    if not refs:
        raise ValueError('At least one human context interval is required')
    raw = _validate_intervals(selected, duration, 'Selected')
    selected_union, reference_union = union(raw), union(refs)
    selected_seconds = sum(end - start for start, end in selected_union)
    reference_seconds = sum(end - start for start, end in reference_union)
    overlap = _overlap_length(selected_union, reference_union)
    coverage = sum(_overlap_length(selected_union, [reference]) / (reference[1] - reference[0]) for reference in refs) / len(refs)
    precision = overlap / selected_seconds if selected_seconds else 0.0
    f1 = 2 * precision * coverage / (precision + coverage) if precision + coverage else 0.0
    complete = sum(any(start <= ref_start and end >= ref_end for start, end in selected_union) for ref_start, ref_end in refs) / len(refs)
    raw_seconds = sum(end - start for start, end in raw)
    return {'metric_schema': 'pitchclipers-context-v1', 'temporal_precision': precision,
            'context_coverage': coverage, 'context_f1': f1, 'complete_context_rate': complete,
            'watch_seconds': selected_seconds, 'raw_window_seconds': raw_seconds,
            'redundant_seconds_removed': raw_seconds - selected_seconds,
            'redundancy': 1 - selected_seconds / raw_seconds if raw_seconds else 0.0,
            'reference_seconds': reference_seconds,
            'notes': 'Context intervals require independent human annotation; metrics are unavailable without references.'}


def fit(records):
    """Validation-only grid fitting for thresholds, not a learned selector."""
    if not records or any(row.get('split') != 'validation' for row in records):
        raise ValueError('Calibration requires explicitly marked validation records')
    ids = [row['match_id'] for row in records]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate match IDs')
    classes = sorted(set(event['class_id'] for row in records for event in row['events']))
    def objective(mapping):
        return float(np.mean([evaluate(clips(row['events'], row['duration'], thresholds=mapping), row['references'], row['duration'])['context_f1'] for row in records]))
    grid = [i / 20 for i in range(21)] + [1.01]
    best = max(grid, key=lambda threshold: (objective(dict.fromkeys(classes, threshold)), threshold))
    mapping = dict.fromkeys(classes, best)
    global_score = objective(mapping)
    for _ in range(3):
        for class_id in classes:
            mapping[class_id] = max(grid, key=lambda threshold: (objective({**mapping, class_id: threshold}), threshold))
    return {'thresholds': mapping, 'global_threshold': best, 'validation_global_f1': global_score, 'validation_class_f1': objective(mapping), 'validation_match_ids': ids, 'method': 'Three-pass coordinate grid search; context F1; 8s before / 5s after'}
