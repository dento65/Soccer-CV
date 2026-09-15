from pathlib import Path
import json, subprocess, uuid, shutil, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pickle
import cv2
from ultralytics import YOLO
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .engine import clips, normalize, evaluate, fit
from .calf_runner import available as calf_available, infer as calf_infer
from .config import ROOT, DATA_DIR, MAX_UPLOAD_BYTES, MAX_VIDEO_SECONDS
from .schemas import ClipPolicy, ExportRequest, PredictionImport, EvaluationRequest
DATA=DATA_DIR; DATA.mkdir(exist_ok=True)
app=FastAPI(title='PitchClipers',version='1.0.0'); pool=ThreadPoolExecutor(max_workers=2); jobs={}
LIVE_TRACKER_WEIGHTS=ROOT/'models'/'yolo11n.pt'

def run(args):
    p=subprocess.run(args,capture_output=True,timeout=1800)
    if p.returncode: raise ValueError(p.stderr.decode(errors='replace')[-1200:])
    return p.stdout

def probe(path):
    info=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
    if not any(s['codec_type']=='video' for s in info['streams']): raise ValueError('No video stream')
    d=float(info['format']['duration'])
    if not 0<d<=MAX_VIDEO_SECONDS: raise ValueError('Video must be between 0 and 10,800 seconds')
    return d

def folder(mid):
    if len(mid)!=32 or any(c not in '0123456789abcdef' for c in mid): raise HTTPException(404,'Match not found')
    p=DATA/mid
    if not (p/'match.json').exists(): raise HTTPException(404,'Match not found')
    return p

def read(mid): return json.loads((folder(mid)/'match.json').read_text())
def save(p,m):
    temp=p/'match.tmp'; temp.write_text(json.dumps(m)); temp.replace(p/'match.json')
def create(path,name):
    duration=probe(path); mid=uuid.uuid4().hex; p=DATA/mid; p.mkdir(); shutil.move(str(path),p/'source.mp4')
    m=dict(id=mid,name=name,duration=duration,events=[],source='Not analyzed',video_url=f'/api/matches/{mid}/video'); save(p,m); return m

@app.get('/api/health')
def health(): return {'status':'ok','ffmpeg':bool(shutil.which('ffmpeg'))}
@app.get('/api/models')
def models():
    ready, detail = calf_available()
    return {'action_spotting': {'name':'SoccerNet CALF benchmark', 'ready':ready, 'detail':detail}}
@app.get('/api/matches')
def matches(): return [json.loads(p.read_text()) for p in sorted(DATA.glob('*/match.json'),key=lambda p:p.stat().st_mtime,reverse=True)]
@app.post('/api/sample')
def sample():
    temp=DATA/(uuid.uuid4().hex+'.mp4'); shutil.copy(DATA/'sample.mp4',temp); return create(temp,'Training ground · supplied sample')
@app.post('/api/upload')
def upload(file:UploadFile):
    temp=DATA/(uuid.uuid4().hex+'.upload')
    try:
        size=0
        with temp.open('wb') as f:
            while chunk:=file.file.read(1024*1024):
                size+=len(chunk)
                if size>MAX_UPLOAD_BYTES: raise ValueError('Maximum upload size is 2 GB')
                f.write(chunk)
        return create(temp,file.filename or 'Uploaded match')
    except Exception as e: temp.unlink(missing_ok=True); raise HTTPException(400,str(e))
@app.get('/api/matches/{mid}')
def get_match(mid:str): return read(mid)
@app.get('/api/matches/{mid}/video')
def video(mid:str): return FileResponse(folder(mid)/'source.mp4',media_type='video/mp4')

def analyze(mid,jid):
    started=time.perf_counter()
    try:
        p=folder(mid); m=read(mid); jobs[jid].update(progress=15)
        proc=subprocess.Popen(['ffmpeg','-v','error','-i',str(p/'source.mp4'),'-vf','fps=2,scale=96:54','-pix_fmt','gray','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        motion=[]; prev=None
        while True:
            raw=proc.stdout.read(96*54)
            if len(raw)!=96*54: break
            frame=np.frombuffer(raw,dtype=np.uint8).astype(float)
            motion.append(float(np.mean(abs(frame-prev))) if prev is not None else 0); prev=frame
        if proc.wait()!=0: raise ValueError('Video decoding failed')
        jobs[jid].update(progress=75)
        x=np.array(motion); lo,hi=np.percentile(x,[10,95]); scores=np.clip((x-lo)/max(hi-lo,1e-6),0,1)
        selected=[]
        for i in np.argsort(-scores):
            if scores[i]<.25: break
            t=float(i)/2
            if all(abs(t-r['timestamp_sec'])>=6 for r in selected): selected.append(dict(event_id=f'a{i}',timestamp_sec=t,class_id='activity',confidence=round(float(scores[i]),4)))
            if len(selected)>=100: break
        m.update(events=sorted(selected,key=lambda e:e['timestamp_sec']),source='Frame-difference activity baseline · not semantic event predictions',analysis_seconds=round(time.perf_counter()-started,3),signal=[round(float(v),3) for v in scores]); save(p,m)
        jobs[jid].update(status='complete',progress=100,result=m)
    except Exception as e: jobs[jid].update(status='failed',error=str(e))
@app.post('/api/matches/{mid}/analyze')
def start(mid:str):
    folder(mid)
    if any(j.get('match_id')==mid and j['status']=='running' for j in jobs.values()): raise HTTPException(409,'Analysis already running')
    jid=uuid.uuid4().hex; jobs[jid]=dict(status='running',progress=0,match_id=mid); pool.submit(analyze,mid,jid); return {'job_id':jid}

def spot_with_calf(mid, jid):
    try:
        p=folder(mid); m=read(mid); jobs[jid].update(progress=5,stage='Extracting ResNet-152 visual features')
        events=calf_infer(p/'source.mp4', p)
        jobs[jid].update(progress=95,stage='Writing 17-class SoccerNet predictions')
        m.update(events=events, source='SoccerNet CALF benchmark: ResNet-152 features + context-aware action spotting', model='CALF_benchmark')
        save(p,m); jobs[jid].update(status='complete',progress=100,result=m)
    except Exception as e: jobs[jid].update(status='failed',error=str(e))

@app.post('/api/matches/{mid}/spot')
def spot(mid:str):
    folder(mid)
    ready, detail=calf_available()
    if not ready: raise HTTPException(503,detail)
    if any(j.get('match_id')==mid and j['status']=='running' for j in jobs.values()): raise HTTPException(409,'Another analysis is already running')
    jid=uuid.uuid4().hex; jobs[jid]=dict(status='running',progress=0,match_id=mid,stage='Queued official CALF inference'); pool.submit(spot_with_calf,mid,jid); return {'job_id':jid,'model':'SoccerNet CALF benchmark'}

def legacy_tracker_summary(mid):
    """Reuse the supplied Football Analytics ByteTrack result for its supplied sample."""
    m=read(mid)
    if m['name'] != 'Training ground · supplied sample':
        raise ValueError('Tracker analytics are available for the supplied Football Analytics sample. Install a compatible player/ball detector to analyze a new upload.')
    stub=ROOT/'assets'/'football_analytics'/'track_stubs.pkl'
    if not stub.exists(): raise ValueError('Football Analytics tracking stub is unavailable')
    tracks=pickle.load(stub.open('rb'))
    fps=len(tracks['players'])/m['duration']
    frames=[]
    possession=[]; offside_frames=0
    for i, frame in enumerate(tracks['players']):
        ball=tracks['ball'][i].get(1,{}).get('bbox')
        owner = owner_for_ball(frame, ball)
        line = offside_line(frame)
        if line is not None: offside_frames += 1
        if owner is not None: possession.append(owner)
        frames.append({'time_sec':round(i/fps,2),'players':len(frame),'referees':len(tracks['referees'][i]),'ball_visible':bool(ball),'ball_owner':owner,'offside_line_x':line})
    return {'source':'Football Analytics ByteTrack detections for the supplied sample', 'frame_count':len(frames), 'fps':round(fps,2), 'mean_players':round(float(np.mean([x['players'] for x in frames])),1), 'ball_visibility':round(float(np.mean([x['ball_visible'] for x in frames])),3), 'control_frames':len(possession), 'offside_cue_frames':offside_frames, 'samples':frames[::max(1,len(frames)//30)]}

def box_center(box):
    return ((float(box[0])+float(box[2]))/2, (float(box[1])+float(box[3]))/2)

def owner_for_ball(players, ball):
    """Nearest tracked player to ball; a transparent geometric possession cue."""
    if not ball or not players: return None
    bx, by = box_center(ball); best = (1e18, None)
    for pid, item in players.items():
        x1,y1,x2,y2 = map(float,item['bbox']); px=(x1+x2)/2; py=y2
        d=((px-bx)**2+(py-by)**2)**.5
        if d < best[0]: best=(d, int(pid))
    return best[1] if best[0] < 150 else None

def offside_line(players):
    """Second-deepest player x-coordinate: visualization cue, not a Laws decision."""
    xs=sorted((box_center(item['bbox'])[0] for item in players.values()), reverse=True)
    return round(xs[1],1) if len(xs) >= 2 else None

def render_tracking_video(mid):
    """Render the supplied ByteTrack result onto its matching supplied sample."""
    p=folder(mid); output=p/'tracking_overlay.mp4'
    if output.exists(): return output
    m=read(mid)
    if m['name'] != 'Training ground · supplied sample':
        raise ValueError('Detection overlay is packaged for the supplied sample. Upload support can be added with a detector checkpoint.')
    tracks=pickle.load((ROOT/'assets'/'football_analytics'/'track_stubs.pkl').open('rb'))
    cap=cv2.VideoCapture(str(p/'source.mp4'))
    fps=cap.get(cv2.CAP_PROP_FPS) or 25; width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    temp=p/'tracking_overlay_raw.mp4'; writer=cv2.VideoWriter(str(temp),cv2.VideoWriter_fourcc(*'mp4v'),fps,(width,height))
    index=0
    try:
        while True:
            ok, frame=cap.read()
            if not ok: break
            ti=min(index,len(tracks['players'])-1); players=tracks['players'][ti]; ball=tracks['ball'][ti].get(1,{}).get('bbox'); owner=owner_for_ball(players,ball); line=offside_line(players)
            for pid,item in players.items():
                x1,y1,x2,y2=map(int,item['bbox']); color=(72,220,110) if int(pid)==owner else (246,190,64)
                cv2.rectangle(frame,(x1,y1),(x2,y2),color,2); cv2.putText(frame,f'P{int(pid)}'+('  CONTROL' if int(pid)==owner else ''),(x1,max(22,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.55,color,2,cv2.LINE_AA)
            for _,item in tracks['referees'][ti].items():
                x1,y1,x2,y2=map(int,item['bbox']); cv2.rectangle(frame,(x1,y1),(x2,y2),(235,235,235),2); cv2.putText(frame,'REF',(x1,max(22,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.5,(235,235,235),2,cv2.LINE_AA)
            if ball:
                x1,y1,x2,y2=map(int,ball); cv2.rectangle(frame,(x1,y1),(x2,y2),(50,130,255),3); cv2.putText(frame,'BALL',(x1,max(22,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.5,(50,130,255),2,cv2.LINE_AA)
            if line is not None:
                x=int(line); cv2.line(frame,(x,0),(x,height),(64,85,255),2); cv2.putText(frame,'OFFSIDE LINE (cue)',(min(x+8,width-240),35),cv2.FONT_HERSHEY_SIMPLEX,.65,(64,85,255),2,cv2.LINE_AA)
            cv2.rectangle(frame,(14,height-55),(580,height-14),(14,20,34),-1)
            cv2.putText(frame,'Player / ball tracking | green = ball control | red = geometric offside line',(26,height-28),cv2.FONT_HERSHEY_SIMPLEX,.55,(255,255,255),1,cv2.LINE_AA)
            writer.write(frame); index += 1
    finally:
        cap.release(); writer.release()
    run(['ffmpeg','-v','error','-y','-i',str(temp),'-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(output)])
    temp.unlink(missing_ok=True); return output

def render_live_tracking_video(mid):
    """Run a packaged YOLO11 detector and ByteTrack association on any uploaded video."""
    p=folder(mid); output=p/'tracking_overlay.mp4'
    if output.exists(): return output
    if not LIVE_TRACKER_WEIGHTS.exists():
        raise ValueError('YOLO11 detector weights are missing from models/yolo11n.pt')
    cap=cv2.VideoCapture(str(p/'source.mp4'))
    fps=cap.get(cv2.CAP_PROP_FPS) or 25; width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); total=max(1,int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    temp=p/'tracking_overlay_raw.mp4'; writer=cv2.VideoWriter(str(temp),cv2.VideoWriter_fourcc(*'mp4v'),fps,(width,height)); model=YOLO(str(LIVE_TRACKER_WEIGHTS)); samples=[]; frame_number=0; visible=control=0
    try:
        while True:
            ok, frame=cap.read()
            if not ok: break
            result=model.track(frame, persist=True, classes=[0,32], conf=.18, iou=.5, verbose=False)[0]
            players={}; ball=None
            if result.boxes is not None:
                for i,box in enumerate(result.boxes):
                    cls=int(box.cls[0]); xyxy=box.xyxy[0].cpu().tolist()
                    if cls==0:
                        pid=int(box.id[0]) if box.id is not None else i+1; players[pid]={'bbox':xyxy}
                    elif cls==32 and (ball is None or float(box.conf[0])>ball[0]): ball=(float(box.conf[0]),xyxy)
            ball_box=ball[1] if ball else None; owner=owner_for_ball(players,ball_box); line=offside_line(players)
            visible+=bool(ball_box); control+=owner is not None
            for pid,item in players.items():
                x1,y1,x2,y2=map(int,item['bbox']); color=(72,220,110) if pid==owner else (246,190,64)
                cv2.rectangle(frame,(x1,y1),(x2,y2),color,2); cv2.putText(frame,f'P{pid}'+(' CONTROL' if pid==owner else ''),(x1,max(22,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.5,color,2,cv2.LINE_AA)
            if ball_box:
                x1,y1,x2,y2=map(int,ball_box); cv2.rectangle(frame,(x1,y1),(x2,y2),(50,130,255),3); cv2.putText(frame,'BALL',(x1,max(22,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.5,(50,130,255),2,cv2.LINE_AA)
            if line is not None:
                x=int(line); cv2.line(frame,(x,0),(x,height),(64,85,255),2); cv2.putText(frame,'OFFSIDE LINE (cue)',(min(x+8,width-240),35),cv2.FONT_HERSHEY_SIMPLEX,.65,(64,85,255),2,cv2.LINE_AA)
            cv2.rectangle(frame,(14,height-55),(660,height-14),(14,20,34),-1); cv2.putText(frame,'YOLO11 + ByteTrack | green = ball control | red = geometric offside line',(26,height-28),cv2.FONT_HERSHEY_SIMPLEX,.55,(255,255,255),1,cv2.LINE_AA)
            writer.write(frame)
            if frame_number % max(1,int(fps))==0: samples.append({'time_sec':round(frame_number/fps,2),'players':len(players),'ball_visible':bool(ball_box),'ball_owner':owner,'offside_line_x':line})
            frame_number+=1
    finally:
        cap.release(); writer.release()
    run(['ffmpeg','-v','error','-y','-i',str(temp),'-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(output)])
    temp.unlink(missing_ok=True)
    return output, {'source':'YOLO11 COCO detector + ByteTrack association', 'frame_count':frame_number, 'fps':round(fps,2), 'mean_players':round(float(np.mean([x['players'] for x in samples])) if samples else 0,1), 'ball_visibility':round(visible/max(frame_number,1),3), 'control_frames':control, 'offside_cue_frames':sum(x['offside_line_x'] is not None for x in samples), 'samples':samples}

@app.get('/api/matches/{mid}/analytics')
def analytics(mid:str):
    live=folder(mid)/'live_tracking.json'
    if live.exists(): return json.loads(live.read_text())
    try: return legacy_tracker_summary(mid)
    except ValueError as e: raise HTTPException(400,str(e))
@app.post('/api/matches/{mid}/tracking-video')
def tracking_video(mid:str):
    try:
        if read(mid)['name'] == 'Training ground · supplied sample':
            render_tracking_video(mid)
        else:
            _, result=render_live_tracking_video(mid)
            (folder(mid)/'live_tracking.json').write_text(json.dumps(result))
        return {'video_url':f'/api/matches/{mid}/tracking-video/file'}
    except ValueError as e: raise HTTPException(400,str(e))
@app.get('/api/matches/{mid}/tracking-video/file')
def tracking_video_file(mid:str):
    path=folder(mid)/'tracking_overlay.mp4'
    if not path.exists(): raise HTTPException(404,'Generate the tracking overlay first')
    return FileResponse(path,media_type='video/mp4',filename='pitchclipers-tracking-overlay.mp4')
@app.get('/api/jobs/{jid}')
def job(jid:str):
    if jid not in jobs: raise HTTPException(404,'Job not found')
    return jobs[jid]
@app.post('/api/matches/{mid}/predictions')
def predictions(mid:str,body:PredictionImport):
    m=read(mid)
    try: m.update(events=normalize(body.payload,m['duration'],body.half),source=body.source,signal=[])
    except (ValueError,KeyError,TypeError) as e: raise HTTPException(400,str(e))
    save(folder(mid),m); return m
@app.post('/api/matches/{mid}/clips')
def candidates(mid:str,body:ClipPolicy):
    m=read(mid); return clips(m['events'],m['duration'],**body.model_dump())
@app.post('/api/matches/{mid}/evaluate')
def evaluation(mid:str,body:EvaluationRequest):
    try: return evaluate(body.clips,body.references,read(mid)['duration'])
    except (ValueError,KeyError,TypeError) as e: raise HTTPException(400,str(e))
@app.post('/api/calibrate')
def calibrate(records:list[dict]):
    try: return fit(records)
    except (ValueError,KeyError,TypeError) as e: raise HTTPException(400,str(e))
def export_worker(mid,jid,rows):
    p=folder(mid); work=p/jid; work.mkdir()
    try:
        for i,c in enumerate(rows):
            run(['ffmpeg','-v','error','-y','-ss',str(c['start_sec']),'-i',str(p/'source.mp4'),'-t',str(c['end_sec']-c['start_sec']),'-map','0:v:0','-map','0:a?','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(work/f'{i}.mp4')]); jobs[jid]['progress']=int((i+1)/len(rows)*90)
        (work/'list.txt').write_text('\n'.join(f"file '{i}.mp4'" for i in range(len(rows))))
        run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(work/'list.txt'),'-c','copy','-movflags','+faststart',str(work/'highlights.mp4')])
        (work/'manifest.json').write_text(json.dumps({'match_id':mid,'source':read(mid)['source'],'clips':rows},indent=2))
        jobs[jid].update(status='complete',progress=100,url=f'/api/matches/{mid}/exports/{jid}')
    except Exception as e: jobs[jid].update(status='failed',error=str(e))
@app.post('/api/matches/{mid}/export')
def export(mid:str,body:ExportRequest):
    m=read(mid)
    try:
        for c in body.clips:
            if not 0<=float(c['start_sec'])<float(c['end_sec'])<=m['duration']: raise ValueError('Invalid clip boundaries')
    except (KeyError,ValueError,TypeError) as e: raise HTTPException(400,str(e))
    jid=uuid.uuid4().hex; jobs[jid]=dict(status='running',progress=0); pool.submit(export_worker,mid,jid,body.clips); return {'job_id':jid}
@app.get('/api/matches/{mid}/exports/{jid}')
def download(mid:str,jid:str):
    if len(jid)!=32 or any(c not in '0123456789abcdef' for c in jid): raise HTTPException(404)
    path=folder(mid)/jid/'highlights.mp4'
    if not path.exists(): raise HTTPException(404)
    return FileResponse(path,media_type='video/mp4',filename='pitchclipers-highlights.mp4')
if (ROOT/'dist').exists(): app.mount('/',StaticFiles(directory=ROOT/'dist',html=True),name='frontend')
