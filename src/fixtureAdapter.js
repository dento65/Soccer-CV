import { buildClipCandidates, filterAndSortEvents, formatEventLabel } from "./eventProcessing";

const FIXTURE_DURATION_SEC = 90 * 60;

const FIXTURE_EVENTS = [
  { event_id: "fixture-goal-1", class_id: "goal", timestamp_sec: 842, confidence: 0.94 },
  { event_id: "fixture-shot-1", class_id: "shot", timestamp_sec: 831, confidence: 0.79 },
  { event_id: "fixture-foul-1", class_id: "foul", timestamp_sec: 1510, confidence: 0.72 },
  { event_id: "fixture-yellow-1", class_id: "yellow_card", timestamp_sec: 1531, confidence: 0.88 },
  { event_id: "fixture-penalty-1", class_id: "penalty", timestamp_sec: 2780, confidence: 0.86 },
  { event_id: "fixture-shot-2", class_id: "shot", timestamp_sec: 2811, confidence: 0.68 },
  { event_id: "fixture-red-1", class_id: "red_card", timestamp_sec: 3942, confidence: 0.63 },
  { event_id: "fixture-foul-2", class_id: "foul", timestamp_sec: 5124, confidence: 0.77 },
];

const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function scaleEvents(durationSec) {
  const scale = Math.max(1, Number(durationSec) || FIXTURE_DURATION_SEC) / FIXTURE_DURATION_SEC;
  return FIXTURE_EVENTS.map((event) => ({
    ...event,
    timestamp_sec: event.timestamp_sec * scale,
    label: formatEventLabel(event.class_id),
    source: "fixture",
  }));
}

export async function runFixtureProcessing({
  durationSec,
  selectedTypeIds,
  onProgress,
  onEvent,
  onLog,
}) {
  const safeDuration = Math.max(1, Number(durationSec) || FIXTURE_DURATION_SEC);
  onLog?.({ type: "fixture_started", message: "Local fixture adapter started" });
  onProgress?.(8, "Preparing local video");
  await wait(120);
  onProgress?.(35, "Loading deterministic event fixture");
  await wait(120);

  // Keep the complete selected-class set so the UI can adjust the threshold live.
  const events = filterAndSortEvents(scaleEvents(safeDuration), { selectedTypeIds, threshold: 0 });
  const clips = buildClipCandidates(events, safeDuration);
  events.forEach((event) => onEvent?.(event));
  onLog?.({ type: "fixture_events_ready", message: `${events.length} fixture events generated` });
  onProgress?.(78, "Building event-centered windows");
  await wait(120);
  onProgress?.(100, "Local fixture processing complete");
  onLog?.({ type: "fixture_completed", message: `${clips.length} clip candidates ready` });

  return {
    schema_version: "1.0",
    match_id: "local-demo",
    duration_sec: safeDuration,
    source: "fixture",
    events,
    clips,
  };
}

export { FIXTURE_EVENTS, FIXTURE_DURATION_SEC };
