# PitchClipers

**PitchClipers** is a local, end-to-end computer-vision demo for football event spotting, context-aware highlight construction, player/ball tracking, and MP4 highlight export.

![Local only](https://img.shields.io/badge/runtime-local%20only-163c2b) ![Python](https://img.shields.io/badge/python-3.11-blue) ![Docker](https://img.shields.io/badge/docker-compose-2496ED)

## One command to start

```bash
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000). Docker stores uploaded videos and generated overlays in `./data` on the host.

> The first build downloads CPU Python dependencies. The repository includes the YOLO11 detector and released CALF checkpoint required by the demo.

## Demo video

Watch [the 16-second walkthrough](demo/pitchclipers_walkthrough.mp4): upload a suitable video, run tracking, inspect the overlay, and create a highlight reel.

## What the application does

1. **Upload a video** - the UI first explains that local processing is intended for MP4 broadcast clips under one minute, captured from a wide pitch view.
2. **Find football events (CALF)** - runs the released SoccerNet CALF action-spotting pipeline: ResNet-152 descriptors, PCA-512, and 17 action classes.
3. **Detect players + ball** - applies YOLO11 COCO detections and ByteTrack association on uploads, then renders a player/ball tracking overlay.
4. **Build a highlight reel** - creates event-centred windows, merges overlap, lets the user edit context, and exports the chosen clips to one MP4.

The full-screen processing state locks controls during a job, preventing duplicate inference or export requests.

## Reproducible local setup without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci
npm run build
PYTHONPATH=. uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Requirements: Python 3.11, Node 20+, FFmpeg. The CALF feature extractor downloads ImageNet ResNet-152 weights only if they are not already cached.

## Repository structure

```text
backend/
  app.py               FastAPI routes and job lifecycle
  calf_runner.py       Adapter for released SoccerNet CALF inference
  engine.py            Detector-independent clip construction and Context Utility
  config.py            Runtime paths and resource limits
  schemas.py           Validated API request models
  services/
    experiments.py     Pilot-run result collection
scripts/
  collect_pilot_results.py  Rebuilds experiments/pilot_runs.json
demo/
  pitchclipers_walkthrough.mp4
models/yolo11n.pt      Local YOLO11 detector
third_party/sn-spotting/   Released CALF implementation and checkpoint
src/                   React interactive interface
report/                CVPR short-paper source
output/pdf/             Final report PDF
```

## Pilot runs and evidence

Run the auditable pilot collector after using the app:

```bash
PYTHONPATH=. python scripts/collect_pilot_results.py
```

It writes `experiments/pilot_runs.json` from completed local tracking runs. The collected fields are runtime/pipeline sanity checks, not accuracy claims. The supplied wide-pitch sample produced cached Football Analytics tracks with 20.4 players/frame, 35.1% ball visibility, and 231 ball-control-cue frames. On the 17-second uploaded `Untitled design.mp4`, the local YOLO11+ByteTrack path completed with 10.3 players/frame; the ball was not detected, which is recorded as 0% visibility rather than inferred possession.

## Research scope and limits

The report proposes a learned context selector and Context Utility metric. The working demo provides pretrained event proposals and an interactive baseline decoder. The red offside line is a **geometric visual cue**, not a Laws-of-the-Game offside decision: a validated decision needs calibrated pitch coordinates, team assignment, attacking direction, and the pass instant. COCO ball detection can miss small or occluded broadcast balls, so missing ball detections remain explicit.

## Validation performed

- `npm test` - 5 frontend/unit tests pass.
- `python -m py_compile backend/*.py backend/services/*.py` - backend syntax passes.
- Browser-tested supplied sample and `Untitled design.mp4`: upload, tracking overlay, active-moment proposals, MP4 export, and duplicate-click lock.
- `unzip -t` is run for the final submission archive.

## Submission files

- `output/pdf/pitchclipers_report.pdf` - short paper.
- `demo/pitchclipers_walkthrough.mp4` - walkthrough video.
- `../PitchClipers_Submission_FINAL_v2.zip` - complete upload-ready project package, including code, Docker setup, report source/PDF, local models, and the walkthrough MP4.
# Soccer-CV

## Redeploy on the EC2 demo instance

After pushing changes to `main`, open **EC2 → Instances → pitchclipers-demo → Connect → EC2 Instance Connect**, then run:

```bash
sudo bash /opt/pitchclipers/deploy/redeploy-ec2.sh
```

The public URL remains the same while the instance is running. The Docker rebuild can take several minutes on the free-plan instance.
