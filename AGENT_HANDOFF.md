# PitchClipers Agent Handoff

## 2026-09-16 implementation update

- The local app at `http://127.0.0.1:8000` now runs the rebuilt policy-oriented interface. Browser verification covered sample loading, active-moment inference, duration-budget policy change, locked controls, completion dialog and MP4 export.
- `backend/engine.py` has asymmetric/symmetric windows, a deterministic overlap-aware duration-budget policy, provenance and validated context metrics. `backend/test_engine.py` supplies regression coverage.
- CALF's fixed upstream output path is serialized. Tracking and export use the asynchronous job lifecycle, reject concurrent match operations, and expose cache behavior. The tracking cache-return bug is fixed.
- Overlay labels nearest-player proximity and screen-space position. They must not be described as possession or offside decisions.
- Real artifacts are in `evaluation/decoder_sweep.{json,csv}`. A fresh `VIDEO.MP4` tracking run took 107.352 seconds for 750 frames, with 6.2 mean players per sampled frame and ball evidence in 1/750 frames. `scripts/run_experiments.py` rebuilds the decoder sweep.
- Presentation deliverables are in `presentation/`, including `PitchClipers_CV_Presentation.pptx`, notes, demo script and Q&A. The deck was structurally validated and rendered for visual review.
- `report/paper.tex` has been revised with recorded evidence. This host has no TeX compiler and its Docker daemon is unavailable, so regenerate the PDF on an environment with TeX before treating the existing PDF as current.

**Project:** PitchClipers / Soccer-CV  
**Repository:** https://github.com/dento65/Soccer-CV  
**Current commit:** `67bac08` — `Polish upload guidance and highlight results`  
**Public demo:** http://54.236.7.220/  
**Primary contact / author shown in the report:** Zaid Rafi

This document is for the next coding agent. It records what is working, where the important code lives, the exact deployed configuration, and the limits that must remain clear in both the app and report.

## Current product state

PitchClipers is a local-first football computer-vision demo. A user can:

1. Load the supplied 30-second football sample or upload an MP4.
2. Run SoccerNet CALF event spotting.
3. Run player/ball tracking and view the tracking overlay.
4. Review detected events as time windows.
5. Select windows and export a combined MP4 highlight reel.

The app is in a submission-ready state. The UI is designed for a short live demo, not for unattended processing of full football matches.

### Current UI behaviour

- The upload area visibly says: **Keep video under 30 seconds.**
- The upload popup recommends MP4 and a wide broadcast/full-pitch view with multiple players visible.
- A full-screen processing overlay locks controls while an upload, inference, overlay render, or MP4 export is running. This prevents double clicks and duplicate jobs.
- After event spotting, a completion popup reports the number of event proposals and the number of merged, exportable clips.
- If events overlap in time, the app intentionally merges their windows into one highlight card. For example, a CALF run can produce two event proposals but one combined clip.
- The export button is disabled until at least one clip exists.
- The labels “INTERACTIVE COMPUTER-VISION DEMO” and “LOCAL CV DEMO” were deliberately removed from the header/hero.

## Architecture

```text
React browser UI
    |
    | HTTP requests and job polling
    v
FastAPI backend (backend/app.py)
    |                     |
    |                     +-- CALF action spotting
    |                     |   released SoccerNet inference code
    |                     |
    |                     +-- YOLO11 + ByteTrack tracking overlay
    |                     |
    |                     +-- FFmpeg clip creation and MP4 export
    v
data/<match-id>/  per-upload video, job artifacts, overlays, exports
```

### Frontend

| Path | Responsibility |
| --- | --- |
| `src/App.jsx` | Entire current React user interface and client-side job polling. This file is compact/minified-style but is the source of truth for buttons, modals, clip merging, status text, and UI state. |
| `src/styles.css` | All page, modal, processing overlay, upload-hint, and highlight-card styling. |
| `src/eventProcessing.js` | Reusable event normalization/filtering/clip-window utilities with unit tests. |
| `src/eventProcessing.test.js` | Four tests for event filtering and window merging. |
| `src/fixtureAdapter.js` | Deterministic fixture path used by tests. |
| `src/apiClient.js` | Separate API client helpers. The active UI currently has a small inline `api` helper in `App.jsx`. |

### Backend

| Path | Responsibility |
| --- | --- |
| `backend/app.py` | FastAPI routes; upload validation; async job state; activity fallback; CALF invocation; tracker overlay; analytics; export worker. |
| `backend/calf_runner.py` | Adapter that starts the released CALF external-video inference code and converts its JSON predictions into app events. |
| `backend/engine.py` | Generic event normalization, clip merging, and the context-utility evaluation helpers. |
| `backend/config.py` | Paths and limits. The backend limit remains 10,800 seconds/2 GB; the UI recommendation is 30 seconds for a responsive demo. |
| `backend/schemas.py` | Pydantic request schemas. |
| `backend/services/experiments.py` | Pilot-run result collection. |

### Models and third-party code

| Asset | Purpose |
| --- | --- |
| `third_party/sn-spotting/Benchmarks/CALF/` | Released SoccerNet CALF implementation and checkpoint. |
| `models/yolo11n.pt` | YOLO11 detector weights used by upload tracking. |
| `assets/football_analytics/track_stubs.pkl` | Cached player/ball track data for the supplied sample. |
| `data/sample.mp4` | Supplied football sample. |

## Functional paths and honest interpretation

### A. Find football events (CALF)

The `Find football events (CALF)` button starts `POST /api/matches/{id}/spot`.

1. The backend checks whether the CALF checkpoint and Python dependencies are available.
2. It invokes the released CALF script.
3. CALF extracts ResNet-152 features, uses PCA-reduced features, and writes SoccerNet action predictions.
4. The adapter converts those predictions into event objects with time, label, and confidence.
5. The UI constructs asymmetric windows using the default 8 seconds before and 5 seconds after event timing, merges overlaps, then selects the merged clips by default.

A successful supplied-sample run was tested after the last UI changes. It returned two event proposals that merged into one clip. This is expected decoder behavior, not a missing result.

If CALF fails, inspect:

```text
data/<match-id>/calf/calf.log
```

Common causes:

- CALF dependencies or checkpoint are unavailable.
- The external feature extraction step failed.
- The server lacks enough memory or has a problematic TensorFlow/PyTorch environment.
- A user uploaded a long or unsupported video.

The `Find active moments (fast)` button is a frame-difference fallback. It is useful for demonstrating clip export but **does not assign football event labels**.

### B. Detect players + ball

The tracking button calls `POST /api/matches/{id}/tracking-video`.

For arbitrary uploaded videos, the backend runs YOLO11 person/sports-ball detection and ByteTrack association. It produces:

- Player boxes and persistent IDs.
- Ball boxes when detected.
- A nearest-player-to-ball geometric control cue.
- A second-deepest-player x-coordinate as a red offside geometry cue.
- An MP4 overlay and simple analytics summary.

For the supplied sample, the app uses cached Football Analytics track data from `track_stubs.pkl`.

Important limits that must stay explicit:

- The red offside line is **not an official offside decision**. A proper decision needs calibrated field coordinates, attacking direction, teams, pass timing, and Laws-of-the-Game reasoning.
- Ball detection can miss small or occluded balls. Do not infer possession where no ball was found.
- The cached sample tracker path and the live YOLO11 path are different sources. Do not present their counts as a controlled detector benchmark.

### C. Export MP4 reel

The export button sends selected merged clips to `POST /api/matches/{id}/export`.

The backend uses FFmpeg to cut and concatenate selected time ranges. The client polls the same job endpoint and shows a `Download MP4` link when the export URL is ready.

## API routes worth knowing

| Route | Purpose |
| --- | --- |
| `GET /api/health` | Liveness and FFmpeg availability. |
| `POST /api/sample` | Creates a fresh match from `data/sample.mp4`. |
| `POST /api/upload` | Stores a user video as a new match. |
| `POST /api/matches/{id}/spot` | Starts CALF event spotting. |
| `POST /api/matches/{id}/analyze` | Starts the frame-difference active-moment fallback. |
| `POST /api/matches/{id}/tracking-video` | Produces tracking overlay. |
| `GET /api/matches/{id}/analytics` | Tracking summary. |
| `POST /api/matches/{id}/export` | Starts MP4 reel export. |
| `GET /api/jobs/{job-id}` | Poll job status, progress, result, error, or export URL. |

## Local development

### Preferred local startup

```bash
cd /Users/hayat/Desktop/Study\ TU/LIT_PROJ/pitchclipers
docker compose up --build
```

Open http://127.0.0.1:8000/.

The compose configuration maps local `./data` to `/app/data`, so uploaded videos and generated artifacts remain available after container restarts.

### Non-Docker startup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci
npm run build
PYTHONPATH=. uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Requirements: Python 3.11, Node 20+, FFmpeg, and enough disk space for model dependencies. CALF can download visual-backbone weights on a fresh machine if not cached.

### Validation commands

Run after a source change:

```bash
npm run build
npm test
python -m py_compile backend/*.py backend/services/*.py
```

The frontend test suite currently has five passing tests. UI-critical flows that were browser-tested:

- Load supplied sample.
- CALF event spotting on the supplied sample.
- Completion popup and merged-clip explanation.
- Upload guidance and cancellation.
- Tracking overlay.
- Active-moment fallback.
- MP4 export.
- Duplicate-click lock during processing.

## Report and submission artifacts

| Path | Content |
| --- | --- |
| `output/pdf/pitchclipers_report.pdf` | Final two-page CVPR-style report. |
| `report/paper.tex` | Source of the report. |
| `demo/pitchclipers_walkthrough.mp4` | Short usage walkthrough. |
| `PitchClipers_Submission_FINAL.zip` / `PitchClipers_Submission.zip` | Existing local submission archives. |
| `SUBMIT_THIS.txt` | Submission reminder. |
| `experiments/pilot_runs.json` | Pilot-runtime records. |

The report author is **Zaid Rafi**. It frames the contribution as context-aware highlight construction: pretrained action proposals, asymmetric windows, overlap merging, and a proposed learned context selector/Context Utility evaluation. Keep claims tied to what the demo and pilot runs actually show.

To refresh pilot records:

```bash
PYTHONPATH=. python scripts/collect_pilot_results.py
```

## Production deployment: EC2

### Current deployment facts

| Field | Value |
| --- | --- |
| AWS instance | `pitchclipers-demo` / `i-0514b3f38a148c166` |
| Public IP | `54.236.7.220` |
| Public URL | http://54.236.7.220/ |
| OS | Amazon Linux 2023 |
| Project checkout | `/home/ec2-user/Soccer-CV` |
| Docker image | `pitchclipers` |
| Container name | `pitchclipers` |
| Host port | 80 |
| Container port | 8000 |
| Persistent match data | `/home/ec2-user/olddata` mounted at `/app/data` |
| Restart policy | `unless-stopped` |

The EC2 server does **not** currently have Docker Compose installed. The README's old command:

```bash
sudo bash /opt/pitchclipers/deploy/redeploy-ec2.sh
```

is stale for this instance because that path does not exist. Do not rely on it until the deployment script is installed and verified.

### Verified deployment procedure used on 2026-09-15

Connect through AWS EC2 Instance Connect as `ec2-user`, then run:

```bash
cd /home/ec2-user/Soccer-CV
git pull origin main
sudo docker build -t pitchclipers /home/ec2-user/Soccer-CV

# Preserve current generated matches and uploads before replacing the container.
sudo docker cp pitchclipers:/app/data /home/ec2-user/olddata

sudo docker rm -f pitchclipers
sudo docker run -d \
  --name pitchclipers \
  -p 80:8000 \
  -v /home/ec2-user/olddata:/app/data \
  --restart unless-stopped \
  pitchclipers

curl http://localhost/api/health
```

Expected health response:

```json
{"status":"ok","ffmpeg":true}
```

For a first deployment where no old container exists, create the persistent data directory instead:

```bash
mkdir -p /home/ec2-user/pitchclipers-data
sudo docker run -d \
  --name pitchclipers \
  -p 80:8000 \
  -v /home/ec2-user/pitchclipers-data:/app/data \
  --restart unless-stopped \
  pitchclipers
```

Then use `/home/ec2-user/pitchclipers-data` consistently for later redeploys.

### Production checks

Run these after deployment:

```bash
sudo docker ps
sudo docker logs pitchclipers
curl http://localhost/api/health
```

Then hard-refresh the public site. A normal browser reload may retain a cached Vite asset; use Ctrl+Shift+R when validating the newest UI.

The last production deployment passed all three checks:

- The container was `Up`.
- Uvicorn logged startup and listened on `0.0.0.0:8000`.
- `curl http://localhost/api/health` returned `{"status":"ok","ffmpeg":true}`.
- The hard-refreshed public UI showed the 30-second upload guidance and no “LOCAL CV DEMO” or “INTERACTIVE COMPUTER-VISION DEMO” labels.

## Recommended next improvements

Prioritize in this order if there is more time:

1. **Make the selector learnable.** Train or fit a small ranking/selection module that predicts clip padding or clip retention from event confidence, temporal context, and tracking features. This addresses the instructor's question about learnable threshold calibration.
2. **Define and evaluate a highlight metric.** Annotate a small match-separated validation set with event, useful build-up, and outcome. Report event coverage, context recall/precision, duplicate viewing duration, and viewer effort at equal total reel duration.
3. **Improve offside analysis.** Add pitch-line calibration, team-color assignment, attacking direction, a pass/ball-contact event, and temporal reasoning. Keep it a research visualization until those pieces are validated.
4. **Improve ball robustness.** Use a football-specific ball detector or fine-tune a detector on broadcast soccer frames. Add temporal interpolation with an explicit confidence state rather than inventing ball locations.
5. **Refactor `src/App.jsx`.** Split it into Upload, Analysis, VideoPlayer, HighlightQueue, and modal components. Preserve the current user behavior while making future changes safer.
6. **Add end-to-end browser tests.** Cover loading the sample, disabled controls while busy, no-proposal state, merged proposals, and MP4 export.
7. **Install a real EC2 deploy script.** Put a script in the actual checkout or use Docker Compose v2, then update README and this document after testing it.

## Guardrails for future changes

- Preserve the explicit distinction between a geometric offside cue and an official offside decision.
- Preserve the distinction between CALF's semantic football events and the non-semantic frame-difference fallback.
- Do not claim accuracy metrics from the cached sample tracks or from a single arbitrary upload.
- Do not remove the processing lock; it prevents duplicate inference and export jobs.
- Keep uploads short in the visible guidance. Thirty seconds is a UX recommendation for the constrained demo server, not the backend's hard file-duration limit.
- Check `calf.log` before changing CALF code when event spotting fails.
- Preserve data before replacing the production container. The current server uses a mounted host directory for this purpose.
