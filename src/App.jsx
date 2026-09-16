import {useEffect, useMemo, useRef, useState} from 'react';
import {Check, Download, Film, HelpCircle, Play, Upload, Users, X} from 'lucide-react';
import './styles.css';

const api = async (path, options={}) => {
  const response = await fetch(path, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw Error(typeof body.detail === 'object' ? body.detail.message : body.detail || 'Request failed');
  return body;
};
const stamp = seconds => new Date(Math.max(0, seconds) * 1000).toISOString().slice(11, 19);
const label = event => (event.label || event.class_id || 'activity').replaceAll('_', ' ');
const color = event => ({goal:'#69e6a6', penalty:'#ef82c8', foul:'#ffc85c', corner:'#7db7ff', clearance:'#ffad72', throw_in:'#7ad9ec', activity:'#b7a5ff'}[event.class_id] || '#d6deea');

function Modal({children, close}) {
  return <div className="modalBackdrop" role="dialog" aria-modal="true" onMouseDown={close}>
    <section className="modal" onMouseDown={event => event.stopPropagation()}>
      <button className="close" aria-label="Close" onClick={close}><X size={18}/></button>{children}
    </section>
  </div>;
}

function UploadPanel({busy, onSample, onUpload}) {
  const input = useRef();
  const [help, setHelp] = useState(false);
  return <>
    <section className="hero">
      <div>
        <p className="eyebrow">FOOTBALL VIDEO ANALYSIS</p>
        <h1>Turn event proposals into compact, explainable clips</h1>
        <p className="lead">Use the supplied match or upload a short wide-view football video. Inspect event confidence, context windows and spatial evidence before exporting.</p>
        <div className="actions">
          <button disabled={busy} onClick={onSample}><Film/> Load supplied sample</button>
          <button disabled={busy} className="secondary" onClick={() => setHelp(true)}><Upload/> Upload video</button>
        </div>
        <p className="hint"><b>Keep video under 30 seconds.</b> This runs locally. A 30-second video usually takes about 1-2 minutes; runtime depends on hardware.</p>
      </div>
      <aside className="workflow"><b>Demo sequence</b><ol><li>Load or upload a video</li><li>Find events or track players and ball</li><li>Adjust clip context and export MP4</li></ol></aside>
    </section>
    {help && <Modal close={() => setHelp(false)}><p className="eyebrow">UPLOAD GUIDE</p><h2>Choose a useful football view</h2><p>Use MP4 when possible. A wide broadcast or full-pitch view gives the detector enough players, pitch and ball context.</p><p>Keep the video under 30 seconds for this local demo. Longer videos may take substantially longer.</p><button onClick={() => {setHelp(false); input.current?.click();}}><Upload/> Choose video</button></Modal>}
    <input ref={input} className="fileInput" type="file" accept="video/*" disabled={busy} onChange={event => {const file=event.target.files?.[0]; event.target.value=''; if(file) onUpload(file);}}/>
  </>;
}

function Timeline({match, events, onSeek}) {
  return <div className="timeline" aria-label="Event timeline">
    <div className="timelineBase"/>{events.map(event => <button key={event.event_id} className="marker" title={`${label(event)} at ${stamp(event.timestamp_sec)}; score ${event.confidence.toFixed(3)}`} style={{left:`${event.timestamp_sec / match.duration * 100}%`, background:color(event)}} onClick={() => onSeek(event.timestamp_sec)}/>)}</div>;
}

function PolicyPanel({policy, setPolicy, threshold, setThreshold, before, setBefore, after, setAfter, budget, setBudget, busy}) {
  return <section className="policyPanel"><div><p className="eyebrow">CLIP POLICY</p><h2>Context and viewing budget</h2></div><div className="policyGrid">
    <label>Selection method<select disabled={busy} value={policy} onChange={e => setPolicy(e.target.value)}><option value="asymmetric">Asymmetric context</option><option value="symmetric">Symmetric baseline</option><option value="budget">Duration budget</option></select></label>
    <label>Minimum score <b>{Math.round(threshold * 100)}%</b><input disabled={busy} type="range" min="0" max="1" step=".05" value={threshold} onChange={e => setThreshold(+e.target.value)}/></label>
    <label>Seconds before<input disabled={busy} type="number" min="0" max="60" value={before} onChange={e => setBefore(+e.target.value)}/></label>
    <label>Seconds after<input disabled={busy || policy==='symmetric'} type="number" min="0" max="60" value={after} onChange={e => setAfter(+e.target.value)}/></label>
    {policy==='budget' && <label>Maximum reel seconds<input disabled={busy} type="number" min="1" max="600" value={budget} onChange={e => setBudget(+e.target.value)}/></label>}
  </div><p className="methodNote">Windows are clipped to the video and merged when they overlap. Budget mode greedily retains proposal score per added viewing second; it is a transparent proxy policy, not a human-quality score.</p></section>;
}

function EventTable({events, clips, selected, toggle, seek, busy}) {
  const selectedIds = new Set(clips.flatMap(clip => clip.event_ids || clip.events.map(event => event.event_id)));
  const byEvent = new Map(clips.flatMap(clip => clip.events.map(event => [event.event_id, clip])));
  return <section className="events"><div><p className="eyebrow">PROPOSALS</p><h2>Event evidence</h2></div>{events.length ? <div className="eventTable">{events.map(event => {const clip=byEvent.get(event.event_id); const isSelected=clip && selected.has(clip.clip_id); return <div className="eventRow" key={event.event_id}><button className="eventDot" style={{background:color(event)}} onClick={() => seek(event.timestamp_sec)} aria-label={`Seek to ${label(event)}`}/><div><b>{label(event)}</b><small>{stamp(event.timestamp_sec)} · raw model score {event.confidence.toFixed(3)}</small></div><span>{selectedIds.has(event.event_id) ? (isSelected ? 'included' : 'available') : 'below policy'}</span>{clip && <button disabled={busy} className="tick" onClick={() => toggle(clip.clip_id)}>{isSelected ? <Check size={16}/> : '+'}</button>}</div>;})}</div> : <p className="empty">No proposals yet. Run football event spotting, or use the non-semantic active-moment fallback.</p>}</section>;
}

function ClipQueue({clips, summary, selected, toggle, selectAll, exportReel, busy, download, seek}) {
  const selectedClips=clips.filter(clip => selected.has(clip.clip_id));
  return <section className="queue"><div className="queueHeader"><div><p className="eyebrow">EXPORT QUEUE</p><h2>{selectedClips.length} selected clip{selectedClips.length===1?'':'s'}</h2></div>{summary && <div className="metrics"><span><b>{summary.union_seconds.toFixed(1)}s</b> union duration</span><span><b>{summary.redundant_seconds_removed.toFixed(1)}s</b> overlap removed</span></div>}</div>
    <div className="queueActions"><button className="secondary" disabled={busy || !clips.length} onClick={selectAll}><Check/> Select all</button><button disabled={busy || !selectedClips.length} onClick={() => exportReel(selectedClips)}><Download/> Export MP4 ({selectedClips.length})</button>{download && <a className="download" href={download} download><Download/> Download MP4</a>}</div>
    <div className="clipCards">{clips.map(clip => <article className={selected.has(clip.clip_id)?'selected':''} key={clip.clip_id} onClick={() => seek(clip.start_sec)}><button className="tick" disabled={busy} onClick={event => {event.stopPropagation(); toggle(clip.clip_id);}}>{selected.has(clip.clip_id)?<Check size={16}/>:''}</button><div><b>{clip.label}</b><small>{stamp(clip.start_sec)} - {stamp(clip.end_sec)} · {clip.duration_sec.toFixed(1)}s</small><small>{clip.selection_reason}</small>{clip.spatial_evidence && <small>Spatial evidence: {clip.spatial_evidence.mean_players} players/sample; ball visible {Math.round(clip.spatial_evidence.ball_visible_fraction*100)}%</small>}</div></article>)}</div>
  </section>;
}

export default function App() {
  const [match, setMatch] = useState(); const [events, setEvents] = useState([]); const [clips, setClips] = useState([]); const [summary,setSummary]=useState();
  const [threshold,setThreshold]=useState(.05); const [before,setBefore]=useState(8); const [after,setAfter]=useState(5); const [policy,setPolicy]=useState('asymmetric'); const [budget,setBudget]=useState(20);
  const [selected,setSelected]=useState(new Set()); const [status,setStatus]=useState('Load a video to begin.'); const [job,setJob]=useState(); const [busy,setBusy]=useState(false); const [analytics,setAnalytics]=useState(); const [trackingUrl,setTrackingUrl]=useState(''); const [showTracking,setShowTracking]=useState(false); const [download,setDownload]=useState(''); const [completion,setCompletion]=useState();
  const video=useRef();
  const load = result => {setMatch(result); setEvents(result.events || []); setClips([]); setSummary(); setSelected(new Set()); setAnalytics(); setTrackingUrl(''); setShowTracking(false); setDownload('');};
  const seek = seconds => {if(video.current) {video.current.currentTime=seconds; video.current.play().catch(() => {});}};
  const createSample = async () => {setBusy(true); try {setStatus('Loading supplied sample...'); load(await api('/api/sample',{method:'POST'})); setStatus('Choose football event spotting or player and ball tracking.');} catch(error) {setStatus(error.message);} finally {setBusy(false);}};
  const upload = async file => {setBusy(true); try {const form=new FormData(); form.append('file',file); setStatus(`Uploading ${file.name}...`); load(await api('/api/upload',{method:'POST',body:form})); setStatus('Upload complete. Choose an analysis path.');} catch(error) {setStatus(error.message);} finally {setBusy(false);}};
  const start = async (operation) => {if(!match || busy) return; setBusy(true); try {const response=await api(`/api/matches/${match.id}/${operation}`,{method:'POST'}); setJob(response.job_id); setStatus('Job queued. Controls stay locked until it finishes.');} catch(error) {setStatus(error.message); setBusy(false);}};
  const exportReel = async rows => {setBusy(true); try {setDownload(''); const response=await api(`/api/matches/${match.id}/export`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clips:rows})}); setJob(response.job_id); setStatus(`Exporting ${rows.length} selected clips...`);} catch(error) {setStatus(error.message); setBusy(false);}};
  useEffect(() => {if(!job) return; const timer=setInterval(async () => {try {const current=await api(`/api/jobs/${job}`); setStatus(`${current.stage || current.operation || 'Processing'} · ${current.status}${current.elapsed_seconds ? ` · ${current.elapsed_seconds}s` : ''}${current.error ? `: ${current.error}` : ''}`); if(current.status !== 'running') {clearInterval(timer); setJob(); setBusy(false); if(current.status==='complete') {if(current.operation==='tracking') {setAnalytics(current.result.analytics); setTrackingUrl(current.result.video_url); setShowTracking(true); setCompletion({title:'Tracking overlay ready',body:'You can inspect player tracks, ball visibility and proximity-control cues.'});} else if(current.operation==='export') {setDownload(current.url); setCompletion({title:'MP4 highlight reel ready',body:'Your selected clips were exported. Use Download MP4 below.'});} else {load(current.result); setCompletion({title:current.operation==='calf'?'Event spotting complete':'Active-moment analysis complete',body:current.result.events?.length ? `${current.result.events.length} proposals are available. Adjust the policy, inspect the timeline, then export selected clips.` : 'No proposals were returned. Try a different video or the active-moment fallback.'});}}}} catch(error) {clearInterval(timer); setBusy(false); setStatus(error.message);}},700); return () => clearInterval(timer);},[job]);
  useEffect(() => {if(!match || !events.length) {setClips([]); return;} const timer=setTimeout(async () => {try {const result=await api(`/api/matches/${match.id}/clips`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({threshold,before,after,policy,budget_seconds:policy==='budget'?budget:null})}); setClips(result.clips); setSummary(result); setSelected(new Set(result.clips.map(clip=>clip.clip_id)));} catch(error) {setStatus(error.message);}},180); return () => clearTimeout(timer);},[match,events,threshold,before,after,policy,budget]);
  const toggle=id => setSelected(current => {const next=new Set(current); next.has(id)?next.delete(id):next.add(id); return next;});
  const source=showTracking&&trackingUrl?trackingUrl:match?.video_url;
  return <main><header><div><b>PITCHCLIPERS</b><small>Context-aware football highlight construction</small></div><span><HelpCircle size={16}/> Event scores are evidence, not final highlights</span></header>
    {!match && <UploadPanel busy={busy} onSample={createSample} onUpload={upload}/>}<p className="status" role="status">{status}</p>
    {busy && <div className="busyOverlay" role="status"><div className="spinner"/><b>{job ? 'Processing video' : 'Working'}</b><span>This runs locally. For a 30-second video, most analyses take about 1-2 minutes. Controls are locked until completion.</span></div>}
    {completion && <Modal close={() => setCompletion()}><p className="eyebrow">COMPLETE</p><h2>{completion.title}</h2><p>{completion.body}</p><button onClick={() => setCompletion()}>Continue</button></Modal>}
    {match && <><section className="workspace"><div className="videoArea"><div className="videoHeader"><div><b>{showTracking?'Tracking overlay':'Source video'}</b><small>{match.name} · {stamp(match.duration)}</small></div><div>{trackingUrl&&<button className="secondary compact" disabled={busy} onClick={() => setShowTracking(value=>!value)}>{showTracking?'Source':'Tracking'} view</button>}</div></div><video ref={video} controls src={source}/>{!showTracking&&<Timeline match={match} events={events} onSeek={seek}/>}<p className="caption">{showTracking?'Green means nearest-player proximity to a detected ball. The red screen-position guide is not an offside decision.':'Click a timeline marker to seek. Proposal confidence is not calibrated highlight quality.'}</p></div>
      <aside className="analysis"><p className="eyebrow">ANALYSIS</p><h2>Choose an output</h2><button disabled={busy} onClick={() => start('spot')}><Play/> Find football events</button><button disabled={busy} className="secondary" onClick={() => start('tracking-video')}><Users/> Track players and ball</button><button disabled={busy} className="secondary" onClick={() => start('analyze')}><Play/> Find active moments</button><small><b>Event spotting</b> uses pretrained SoccerNet CALF. <b>Tracking</b> uses YOLO11 and ByteTrack. Active moments are non-semantic visual motion proposals.</small></aside></section>
      {analytics && <section className="analytics"><div><b>{analytics.mean_players}</b><span>mean players / sampled frame</span></div><div><b>{Math.round(analytics.ball_visibility*100)}%</b><span>ball visible</span></div><div><b>{analytics.control_frames}</b><span>proximity-control frames</span></div><div><b>{analytics.screen_position_guide_frames}</b><span>screen-position samples</span></div><p>{analytics.limitations}</p></section>}
      <PolicyPanel {...{policy,setPolicy,threshold,setThreshold,before,setBefore,after,setAfter,budget,setBudget,busy}}/><EventTable {...{events,clips,selected,toggle,seek,busy}}/><ClipQueue {...{clips,summary,selected,toggle,selectAll:()=>setSelected(new Set(clips.map(clip=>clip.clip_id))),exportReel,busy,download,seek}}/>
    </>}</main>;
}
