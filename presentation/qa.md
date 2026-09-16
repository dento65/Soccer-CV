# Likely Q&A

**What did you implement versus reuse?**

We reuse released pretrained CALF, YOLO11 and ByteTrack. We implemented the context-window policies, overlap-aware interval union, duration-budgeted greedy selector, context-evaluation endpoint, per-clip tracking summaries, job control, cache handling, interactive analysis and MP4 export.

**Why is spotting mAP insufficient?**

Spotting mAP asks whether an event timestamp/class was found near a label. A highlight needs enough before/after context to make the event understandable. The needed context can be long even for a correct timestamp.

**Is the selector learned?**

No. The working budget policy is deterministic. The threshold grid routine is validation parameter fitting, not a trained neural model. A learned selector needs independently annotated clip-sufficiency labels and match-separated evaluation.

**Why does merging matter?**

If nearby proposals each create a window, exporting them separately repeats footage. Merging preserves the same temporal union while reducing repeated viewing time.

**Does the red line detect offside?**

No. It is a screen-position guide. Rules-based offside requires calibrated pitch coordinates, team assignment, attacking direction, the ball and the pass instant.

**What does missing ball evidence mean?**

Only that this detector did not observe the ball. It must not be interpreted as zero possession or no football event.

**How do you avoid leakage?**

Future learned selection must split by match, never by overlapping windows from the same match.

**What are the next steps?**

Collect independent minimal-context annotations, compare policies at equal viewing duration, then test whether tracking features improve context coverage.
