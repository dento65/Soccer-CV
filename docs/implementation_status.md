# Implementation status

Date: 2026-09-16

- `VIDEO.MP4` (30.00 seconds) and `INPUT_VID.MP4` (31.42 seconds) both contain wide broadcast football views with multiple players. The second clip exceeds the local-demo guidance by 1.42 seconds and should be trimmed for a strict under-30-second demonstration.
- CALF inference is serialized because its released external-video script writes a fixed prediction path. Tracking, event spotting, active-moment analysis, and export now share the asynchronous job lifecycle and reject concurrent operations on the same match.
- The decoder implements asymmetric and symmetric context policies plus a deterministic duration-budgeted greedy policy. Context metrics are implemented but remain unavailable for unannotated footage.
- Tracking uses pretrained YOLO11 and ByteTrack. Nearest-player ball proximity and screen-space player position are visualization cues; neither is a possession label or an offside decision.
