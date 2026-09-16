# PitchClipers speaker notes

## Opening

The project asks a narrower question than generic highlight generation: given temporal action proposals, how can we make compact clips that preserve the context a viewer needs? A proposal timestamp has no intrinsic before/after boundary.

## Method

CALF, YOLO11 and ByteTrack are pretrained components. The project implementation is the evidence-to-clip layer: interval policies, merging, duration accounting, a budgeted selector, context-metric API, tracking summaries, export and job reliability.

For a proposal at time `t`, the default interval contains eight seconds before and five seconds after. Windows merge when they overlap. The duration-budgeted policy ranks a proposal by raw action score divided by added union duration. It is deterministic and explainable; it is not a learned preference model.

## Results

The decoder sweep is measured on saved CALF outputs. At score 0.05, two proposals with 4/3 context yield an 11.5-second merged reel. The default 8/5 policy yields 17.5 seconds; it removes 8.5 seconds from 26 raw seconds, or 32.7 percent. The experiment measures policy behavior, not spotting mAP or perceived quality.

The fresh tracking run on `VIDEO.MP4` processed 750 frames in 107.352 seconds. It detected a mean 6.2 players per sampled frame, but a small ball in only one frame. This is useful evidence: detection missingness must remain explicit. The red guide is screen-space geometry, not offside.

## Closing

The next experiment is annotation, not a larger claim. Reviewers define minimal context intervals, then fixed, budgeted and learned policies can be compared at the same viewing duration with match-separated splits.
