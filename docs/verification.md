# Verification record

Date: 2026-09-16

## Automated checks

- `npm test`: 5 existing frontend tests passed.
- `npm run build`: production Vite build passed.
- `./.venv/bin/python -m unittest backend.test_engine -v`: 4 policy and metric tests passed.
- `./.venv/bin/python -m compileall -q backend`: passed.
- FastAPI request checks: health and CALF availability returned success; clip-policy and context-evaluation routes accepted valid payloads.

## Real input and browser checks

- `VIDEO.MP4` was uploaded as a 30.00-second wide-view broadcast clip. Fresh YOLO11+ByteTrack tracking processed 750 frames in 107.352 seconds, yielding 6.2 mean players per sampled frame and a detected ball in 1/750 frames. A repeat cache run completed in 0.003 seconds.
- `INPUT_VID.MP4` was copied into a 30.01-second local-test derivative and uploaded. The derivative is one frame above the under-30-second guidance; use a 29.5-second trim for a strict demo.
- Browser-tested `http://127.0.0.1:8000`: sample loading, active-moment analysis, timeline proposals, asymmetric-to-budget policy transition, queue update, UI lock while processing, completion dialog, and MP4 export.
- The interface export completed in 3.227 seconds for the budgeted 19-second reel. A downloaded H.264 export was also checked with ffprobe and reported 30.000 seconds in the full-reel test.

## Browser acceptance sequence

Remaining manual check before an in-class demo: play the tracking overlay in the current browser after a fresh tracking run. The generated overlay file and cache return were verified by API, but browser playback of that overlay was not repeated after the final server restart.
