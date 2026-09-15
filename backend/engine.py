"""Detector-independent clip construction and context evaluation (seconds)."""
import math
import numpy as np

CLASSES = ['activity','goal','penalty','shot','foul','yellow_card','red_card','corner','offside','substitution','free_kick']
ALIASES = {'shots on target':'shot','shots off target':'shot','yellow card':'yellow_card','red card':'red_card','yellow->red card':'red_card','direct free-kick':'free_kick','indirect free-kick':'free_kick'}

def normalize(payload, duration, half=1):
    rows = payload if isinstance(payload,list) else payload.get('predictions',payload.get('events',[]))
    if not isinstance(rows,list) or len(rows)>100000: raise ValueError('Expected a list of at most 100,000 events')
    result=[]
    for i,r in enumerate(rows):
        if int(r.get('half',half)) != half: continue
        label=str(r.get('class_id',r.get('label','activity'))).lower()
        label=ALIASES.get(label,label.replace(' ','_'))
        t=float(r['timestamp_sec']) if 'timestamp_sec' in r else float(r['position'])/1000
        s=float(r.get('confidence',r.get('score',1)))
        if not math.isfinite(t+s) or not 0<=t<=duration or not 0<=s<=1: raise ValueError(f'Invalid event {i}: timestamp/score outside range')
        result.append(dict(event_id=f'e{i}',class_id=label,timestamp_sec=t,confidence=s))
    return sorted(result,key=lambda r:r['timestamp_sec'])

def clips(events,duration,threshold=.5,before=8,after=5,classes=None,thresholds=None):
    out=[]
    for e in sorted(events,key=lambda x:x['timestamp_sec']):
        if classes is not None and e['class_id'] not in classes: continue
        if e['confidence'] < (thresholds or {}).get(e['class_id'],threshold): continue
        a=max(0,e['timestamp_sec']-before); b=min(duration,e['timestamp_sec']+after)
        if b<=a: continue
        if out and a<=out[-1]['end_sec']:
            out[-1]['end_sec']=max(b,out[-1]['end_sec']); out[-1]['events'].append(e)
        else: out.append(dict(start_sec=a,end_sec=b,events=[e]))
    for i,c in enumerate(out): c['clip_id']=f'c{i}'; c['label']=' + '.join(dict.fromkeys(e['class_id'] for e in c['events']))
    return out

def union(intervals):
    out=[]
    for a,b in sorted(intervals):
        if out and a<=out[-1][1]: out[-1][1]=max(b,out[-1][1])
        else: out.append([a,b])
    return out

def evaluate(selected, references, duration):
    """Reference intervals are human context annotations, not point-label truth."""
    refs=[]
    for r in references:
        a,b=float(r['start_sec']),float(r['end_sec'])
        if not 0<=a<b<=duration: raise ValueError('Reference interval outside video')
        refs.append((a,b))
    if not refs: raise ValueError('At least one human context interval is required')
    u=union([(c['start_sec'],c['end_sec']) for c in selected]); ru=union(refs)
    length=sum(b-a for a,b in u); relevant=sum(b-a for a,b in ru)
    overlap=sum(max(0,min(b,d)-max(a,c)) for a,b in u for c,d in ru)
    coverage=sum(max([max(0,min(b,d)-max(a,c))/(d-c) for a,b in u] or [0]) for c,d in refs)/len(refs)
    precision=overlap/length if length else 0
    f1=2*precision*coverage/(precision+coverage) if precision+coverage else 0
    raw=sum(c['end_sec']-c['start_sec'] for c in selected)
    return dict(context_coverage=coverage,temporal_precision=precision,context_f1=f1,complete_context_rate=sum(any(a<=c and b>=d for a,b in u) for c,d in refs)/len(refs),redundancy=1-length/raw if raw else 0,watch_seconds=raw,reference_seconds=relevant)

def fit(records):
    """Validation-only empirical risk minimization; never accepts test records."""
    if not records or any(r.get('split')!='validation' for r in records): raise ValueError('Calibration requires explicitly marked validation records')
    ids=[r['match_id'] for r in records]
    if len(set(ids))!=len(ids): raise ValueError('Duplicate match IDs')
    classes=sorted(set(e['class_id'] for r in records for e in r['events']))
    def objective(mapping):
        return float(np.mean([evaluate(clips(r['events'],r['duration'],thresholds=mapping),r['references'],r['duration'])['context_f1'] for r in records]))
    grid=[i/20 for i in range(21)]+[1.01]
    best=max(grid,key=lambda t:(objective(dict.fromkeys(classes,t)),t))
    mapping=dict.fromkeys(classes,best); global_score=objective(mapping)
    for _ in range(3):
        for c in classes: mapping[c]=max(grid,key=lambda t:(objective({**mapping,c:t}),t))
    return dict(thresholds=mapping,global_threshold=best,validation_global_f1=global_score,validation_class_f1=objective(mapping),validation_match_ids=ids,method='Three-pass coordinate grid search; context F1; 8s before / 5s after')
