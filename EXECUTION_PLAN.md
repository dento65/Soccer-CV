# PitchClipers: implementation and presentation handoff

## Assignment and intended outcome

Improve this existing football computer-vision project into a reliable, explainable demo with reproducible experiments and an editable presentation. The user explicitly requested this plan for a lighter agent to execute. Work autonomously in this repository; implement and test rather than returning another plan. Do not deploy or incur cloud costs merely to complete this local improvement task.

The academic question is: **How should action-spotting proposals be converted into compact clips that preserve event context, and when can tracking evidence help explain or select those clips?** The contribution should be implemented clip construction, evaluation, and spatial evidence integration, with measured trade-offs. Adding files or frontend decoration alone does not strengthen the CV contribution.

Do not invent benchmark accuracy, annotations, learned parameters, team contributions, or state-of-the-art claims. Present completed work confidently and reserve a small section for limitations. Distinguish reused pretrained models from our implemented methods. Current outputs support system and decoder measurements, not highlight-quality accuracy.

## Working context

- Repository: `/Users/hayat/Desktop/Study TU/LIT_PROJ/pitchclipers`
- Git remote: `https://github.com/dento65/Soccer-CV.git`
- Local application: `http://127.0.0.1:8000/`
- New footage: `/Users/hayat/Downloads/VIDEO.MP4` and `/Users/hayat/Downloads/INPUT_VID.MP4`.
- Earlier probe measured approximately 30.0 seconds and 31.42 seconds respectively. Reconfirm with ffprobe. Preserve originals; create a clearly recorded <=30-second derivative of the latter for the short-upload workflow.
- Existing report: `report/paper.tex`, `report/paper.pdf`, `output/pdf/pitchclipers_report.pdf`. Author must remain **Zaid Rafi**. User requested approximately 1.25 pages of content in a permitted CVPR/NeurIPS format, maximum two pages.
- Earlier handoff: `AGENT_HANDOFF.md`; useful background, but verify assertions against code and current runtime.
- Existing walkthrough: `demo/pitchclipers_walkthrough.mp4`.
- No trustworthy event/context ground-truth dataset has been established for these uploaded videos.

## First actions

1. Read applicable AGENTS.md files, README, this plan and existing handoff. Inspect git status; preserve all user changes.
2. Inspect `backend/app.py`, `backend/calf_runner.py`, `backend/engine.py`, schemas/config, `src/App.jsx`, `src/eventProcessing.js`, `src/apiClient.js`, styles and tests.
3. Record baseline health, model availability, frontend tests/build and Python environment. Use existing `.venv` and installed weights where possible.
4. Inspect a contact sheet from each new video. Record duration, dimensions, fps, camera type and visible content. Do not assume footage is suitable for offside or ball tracking.
5. Save a short baseline status in `docs/implementation_status.md`. Update it as work completes.

## Phase 1 — correctness and repeatable jobs (must finish first)

### Confirmed code risks to fix

- `backend/calf_runner.py` uses CALF's shared prediction output directory and deletes a common Predictions-v2.json. Two workers can race. Prefer isolated per-job inference output if supported; otherwise serialize the complete inference/read/copy operation with an explicit lock. Document single-process limits or use a cross-process lock if multiple server workers are supported. Do not just lock the subprocess and then read outside the lock.
- `render_live_tracking_video()` in `backend/app.py` returns only a Path on a cache hit, but its caller expects `(path, analytics)`. Make cache results consistent and recover sensibly from a missing/stale analytics JSON.
- Tracking currently blocks an HTTP request. Move it to the same job lifecycle as spotting/export, with useful status and failure details. Ensure models are not unintentionally shared across concurrent tracking sessions with persistent tracker state.
- Reject duplicate operations for an already running match/stage; return the active job or a clear conflict. Frontend disabling alone is insufficient.
- Persist stage timings, model identity/configuration and cache status. Distinguish cache load time from fresh inference. Never fabricate percent completion; named stages or indeterminate progress are fine.
- Validate evaluation intervals: finite numbers, ordered bounds, within video duration. Validate malformed model output without corrupting saved state.
- Remove ambiguous analytics units: frame statistics must count frames consistently, not sometimes sampled seconds. Count mean players across all processed frames or label it as a sampled estimate.

### Acceptance

First and repeated runs work; two rapid submissions do not start duplicate inference; CALF results cannot cross-contaminate matches; failed jobs release busy state and allow retry; invalid intervals produce a clear 4xx response. Add focused regression tests for these behaviors using fake runners, without running heavy models in unit tests.

## Phase 2 — a meaningful CV contribution

### A. Explicit clip construction policies

Implement a small tested policy module, keeping current API behavior compatible:

1. Fixed symmetric context baseline.
2. Asymmetric event context (existing 8 seconds before / 5 seconds after default, plus configurable windows).
3. Duration-budgeted proposal selection: choose candidate intervals under a requested viewing-time budget, accounting for overlap by **union duration**, not sum of raw windows. A deterministic greedy marginal-gain-per-added-second algorithm is acceptable; document that it is a heuristic, not an optimal solver.

Represent each clip with stable IDs, constituent event IDs, raw confidence, start/end, duration and selection reason. Sort ties deterministically. Expose a clear confidence-duration trade-off. Do not call raw confidence a calibrated probability.

For the budget policy define the objective explicitly, for example sum of confidence weights of distinct supported events, with optional class weights. Avoid counting overlapping proposals repeatedly. Report that this optimizes a proxy objective, not measured human enjoyment.

### B. Model-independent context evaluation

Extend `backend/engine.py` evaluation and add a small annotation workflow/import format. A reference interval represents the minimum context a reviewer judges necessary for an event; the event timestamp alone cannot establish this.

Report:

- Temporal precision: selected/reference union intersection divided by selected union duration.
- Context coverage: mean fraction of each reference interval covered by the complete selected union. Explicitly distinguish this from coverage by a single uninterrupted clip.
- Complete-context rate: fraction of reference intervals entirely contained in a selected clip.
- Context F1: harmonic mean of temporal precision and coverage, with defined empty cases.
- Viewing duration: selected union duration.
- Redundant duration removed by merging: raw proposal-window duration minus union duration.
- Optional boundary error only with matched annotated references and clearly defined matching.

Name these project-defined measures; do not imply established benchmark status. Add hand-calculated unit cases: disjoint intervals, overlap, fragmentation, clipping at video boundaries, empty sets, invalid values. Export annotations with schema version, video hash, annotator/provenance and timestamps.

### C. Spatial evidence that is defensible

Keep YOLO/ByteTrack overlays, and expose player-count and ball-visibility timelines. Add per-clip summaries (ball visible fraction, player count, track continuity where measurable). Missing ball evidence must remain unknown, never become zero possession or evidence of no event.

Current `offside_line()` uses image x positions of all players. It does not establish teams, attack direction, perspective, ball position or the pass instant. Rename it to a **screen-space player-position guide**, make it optional, and explain its interpretation. Do not call it an offside decision. Likewise label nearest-player ball assignment **proximity-based control estimate**, not verified possession.

Only add team clustering or pitch calibration after core acceptance tests pass and if the footage supports it. True offside is outside the minimum deliverable. A trustworthy explanation is better than an incorrect red line.

### D. Learnable component: conditional extension only

Existing grid threshold calibration is parameter fitting, not a newly trained neural network. A logistic selector is permissible only if real suitability/context annotations and a valid separated evaluation set exist. With only a few independent videos, do not market a fitted selector as generalizable evidence. Never create pseudo-ground-truth from the same detector then report it as accuracy.

Deliver the deterministic budget policy and evaluation workflow even if learned selection is deferred. State the annotation and match-separated evaluation needed for the extension.

## Phase 3 — interface that explains the pipeline

Refactor the giant App.jsx into a few meaningful components/hooks; avoid gratuitous file proliferation. Suggested responsibilities: UploadPanel, ProcessingStatus, VideoWorkspace, EventTimeline, ClipInspector, PolicyComparison and a job-polling hook.

Required workflow:

1. Upload/sample. Upload help popup and persistent concise text: **Use a wide view of the pitch. Keep videos under 30 seconds for this local demo. A 30-second video usually takes about 1–2 minutes; runtime depends on hardware.** Treat timing as an estimate and correct it if measured runs contradict it. Define whether 30 seconds is guidance or an enforced limit; keep backend/UI consistent.
2. Choose action spotting or player/ball tracking; explain each output in one sentence. Motion baseline is clearly labeled non-semantic.
3. Show queued/running stage, elapsed time, disabled duplicate controls and accessible busy feedback.
4. Show source video plus event-score timeline. Click event/clip to seek. Explain threshold effects and empty results. Distinguish no model proposals from proposals hidden by the threshold.
5. Keep seconds-before and seconds-after controls visible, per the user's latest preference. Show budget as an optional selection mode.
6. Show a sortable/readable event table: event, timestamp, confidence, selected/rejected reason, clip bounds. Selected state must reconcile correctly when policy/threshold changes. Disable export when no clips are selected.
7. Compare policies with accepted events, union duration, overlap removed and context metrics only when annotations exist. Mark unannotated metrics unavailable.
8. Completion popup names the actual completed operation. For spotting: events/clips and next step; for tracking: overlay available; for export: download ready. Do not say CALF when motion baseline completed. Zero-result completion must not promise an export.
9. Download MP4 and JSON manifest. Preserve original audio where feasible. Check output duration and browser playback.

Use professional restrained styling, readable contrast and clear hierarchy. Keep technical depth in an expandable method panel, not cluttering primary controls. Keyboard-close dialogs, focus management and mobile layout should work.

## Phase 4 — reproducible experiments on supplied footage

Create `scripts/run_experiments.py` and extend `backend/services/experiments.py` as needed. Run the supplied sample and the two new videos serially for CALF until isolation is verified. Reuse cached model outputs for decoder sweeps but identify them as cached. Store outputs in `evaluation/` (small JSON/CSV/figures only); avoid committing large footage, weights or private paths.

For each video save SHA-256, duration/fps/resolution, processing configuration, model/checkpoint identification, timing/cache status, proposals and tracking summaries. Include failures rather than silently excluding them.

Sweep a compact predefined grid: thresholds 0.05, 0.20, 0.40; context windows (4,3), (8,5), (12,8); and two feasible duration budgets based on video duration. Compare policies at equal duration when claiming a quality difference. Store exact configuration and metric definitions.

Without context annotations, report runtime, proposal counts, retained duration, overlap savings, ball visibility and policy behavior. These are valid measured findings but not accuracy. With reviewed annotations, report context metrics separately, explicitly describing the small pilot and how annotation was obtained. Do not tune on test clips then call the result held-out.

Figures: confidence vs retained duration, policy duration/overlap comparison, player count + ball visibility over time, and one qualitative annotated frame showing supported spatial evidence. Explain at least one failure case from actual footage.

Success means one command reproduces tables from saved outputs, and a documented command reruns inference. Numeric values in report/slides must trace to these artifacts.

## Phase 5 — end-to-end verification

- Run npm tests and production build.
- Run backend unit/regression tests appropriate to changes.
- In the actual browser upload each new clip, run spotting and tracking, inspect results, change threshold/timing/budget, seek events, select/deselect, export, open downloaded MP4.
- Verify repeated tracking uses cache correctly and repeated buttons are blocked.
- Exercise zero events, no ball detections, inference failure, malformed upload and refresh/reopen of saved match.
- Verify a clean startup with the documented command. Build Docker if available; if Docker cannot run, explicitly record that limit rather than claiming a successful container test.
- Record `docs/verification.md`: date, environment, commands, pass/fail, evidence paths and remaining limitations.

Do not declare everything working after unit tests alone. Browser checks plus real exported media are required.

## Phase 6 — presentation and submission package

Use the presentations skill and its required editable-deck/render/verification workflow. Skill path: `/Users/hayat/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations/SKILL.md`. The prior turn read the skill and listed templates, but has not chosen a template or authored slides. Read instructions in the new agent context.

Create an 8–10 minute presentation with approximately 9 main slides plus 3 backup slides:

1. Problem and concrete research question.
2. Why spotting timestamps are insufficient for contextual highlights.
3. Pipeline and precise reused-versus-implemented components.
4. Clip policy: confidence, asymmetric context, overlap, duration budget.
5. Proposed context measures with one simple numerical example.
6. Tracking evidence and missing-ball handling; distinguish spatial guide from offside.
7. Real quantitative experiments with native editable charts.
8. Qualitative success/failure and interpretation.
9. Live demo sequence and conclusion: supported findings + next experiment.

Backup: algorithm/complexity; evaluation/annotation protocol; limitations and Q&A. Include notes explaining choices in plain language and cite the actual pretrained methods. Existing report references include SoccerNet-v2, CALF, ByteTrack, YOLO, NetVLAD++ and ActionFormer; verify primary sources before adding specific claims.

Create `presentation/speaker_notes.md`, `presentation/demo_script.md`, `presentation/qa.md`. Q&A must cover: what we implemented; pretrained components; why highlight quality differs from spotting mAP; why merging matters; threshold calibration versus learned selection; missing ball evidence; offside limitations; dataset leakage; computational constraints; how to extend evaluation.

Record a short real MP4 walkthrough if available tooling permits; show upload, inference status, timeline, policy change, overlay and successful export. Do not simulate successful model outputs. Keep a precomputed result available as a clearly labeled live-demo fallback.

Update the report only after experiments. Keep author Zaid Rafi, concise MS-level explanation, requested length and approved template. Emphasize research question, method, measured findings and one focused limitation; do not devote most space to stack details. Render and inspect the PDF using the PDF skill.

## Documentation and packaging

Root README: prerequisites, one-command startup, model download/cache behavior, expected resources, sample demo sequence, experiment commands, tests, architecture, pretrained/model licenses, and limitations. Docker Compose should persist outputs/model cache and include health checking. Do not promise neural inference on 0.1 CPU / 512 MB RAM.

Update AGENT_HANDOFF.md to actual final state. Check gitignore: no videos, credentials, bulky caches or accidental data directories. Do not change AWS resources as part of local development. Old EC2 information in the prior handoff may be stale; verify before a later requested redeploy. Do not repeat its one-time data migration into an existing folder.

## Priority / stop rules

1. Reliability fixes and real input/export verification.
2. Explicit policy module, context evaluation, spatial evidence summaries.
3. Reproducible measurements and clear comparison UI.
4. Presentation, report and README grounded in those measurements.
5. Optional trained selector, team assignment or homography only with time/data and independent validation.

If a model is blocked, diagnose and expose the failure; keep the working stage usable. Do not substitute motion detection and label it CALF. If a proposed extension cannot be validated, deliver a smaller complete method and label future work.

## Final response expected from executing agent

Provide links to the working app/start instructions, editable deck, report, walkthrough, results and verification record. Summarize substantive CV additions, actual successful tests and specific unresolved limitations. Make no claim about how many people worked on it. The goal is defensible depth and a demo the student can explain.
