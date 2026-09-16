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

1. **Upload a video** - guidance beside the upload button and in the popup recommends MP4 broadcast clips under 30 seconds, captured from a wide pitch view.
2. **Find football events (CALF)** - runs the released SoccerNet CALF action-spotting pipeline: ResNet-152 descriptors, PCA-512, and 17 action classes.
3. **Detect players + ball** - applies YOLO11 COCO detections and ByteTrack association on uploads, then renders a player/ball tracking overlay.
4. **Build a highlight reel** - compares asymmetric and symmetric context windows, or a duration-budgeted greedy policy. It merges overlap, shows selection provenance, lets the user select clips, and exports one MP4.

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
  engine.py            Detector-independent policies and context evaluation
  config.py            Runtime paths and resource limits
  schemas.py           Validated API request models
  services/
    experiments.py     Pilot-run result collection
scripts/
  run_experiments.py        Rebuilds decoder-sensitivity CSV/JSON from saved runs
demo/
  pitchclipers_walkthrough.mp4
models/yolo11n.pt      Local YOLO11 detector
third_party/sn-spotting/   Released CALF implementation and checkpoint
src/                   React interactive interface
report/                CVPR short-paper source
output/pdf/             Final report PDF
```

## Reproducible decoder evidence

Run the auditable pilot collector after using the app:

```bash
./.venv/bin/python scripts/run_experiments.py
```

It writes `evaluation/decoder_sweep.csv` and `evaluation/decoder_sweep.json` from completed named local runs. The script reuses saved proposal outputs and sweeps only the implemented decoder. It records proposal count, union duration and overlap removed. Those are decoder and system measurements, not event-spotting accuracy or human highlight-quality claims.

## Research scope and limits

The working demo provides pretrained event proposals and an interactive decoder. A human-context annotation workflow and a learned selector require independent labelled data and match-separated validation; they are not presented as completed model-training results. The red screen-position guide is not a Laws-of-the-Game offside decision: a validated decision needs calibrated pitch coordinates, team assignment, attacking direction, ball position and the pass instant. COCO ball detection can miss small or occluded broadcast balls, so missing ball detections remain explicit.

## Validation performed

- `npm test` - 5 frontend/unit tests pass.
- `./.venv/bin/python -m unittest backend.test_engine -v` - decoder/context unit tests.
- `./.venv/bin/python -m compileall -q backend` - backend syntax.
- Run the browser verification sequence in `docs/verification.md` before submitting from a new machine.
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
