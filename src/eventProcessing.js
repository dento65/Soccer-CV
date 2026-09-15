export const EVENT_TYPES = [
  { id: "goal", label: "Goal", color: "#16a34a" },
  { id: "penalty", label: "Penalty", color: "#dc2626" },
  { id: "shot", label: "Shot", color: "#2563eb" },
  { id: "foul", label: "Foul", color: "#f59e0b" },
  { id: "yellow_card", label: "Yellow card", color: "#eab308" },
  { id: "red_card", label: "Red card", color: "#b91c1c" },
];

const WINDOW_POLICY = {
  goal: { before: 15, after: 15 },
  penalty: { before: 15, after: 15 },
  default: { before: 8, after: 8 },
};

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

export function normalizeEvent(event, durationSec = Number.POSITIVE_INFINITY) {
  const timestamp = clamp(Number(event.timestamp_sec) || 0, 0, durationSec);
  const confidence = clamp(Number(event.confidence ?? event.score) || 0, 0, 1);
  return {
    ...event,
    event_id: event.event_id || `event-${timestamp}`,
    class_id: event.class_id || event.label?.toLowerCase().replace(/\s+/g, "_") || "unknown",
    label: event.label || event.event_types?.[0] || event.class_id || "Unknown",
    timestamp_sec: timestamp,
    confidence,
    score: confidence,
  };
}

export function filterAndSortEvents(events = [], { selectedTypeIds = [], threshold = 0 } = {}) {
  const selected = new Set(selectedTypeIds);
  return events
    .map((event) => normalizeEvent(event))
    .filter((event) => (!selected.size || selected.has(event.class_id)) && event.confidence >= threshold)
    .sort((a, b) => a.timestamp_sec - b.timestamp_sec);
}

export function createClipWindow(event, durationSec) {
  const policy = WINDOW_POLICY[event.class_id] || WINDOW_POLICY.default;
  const timestamp = clamp(Number(event.timestamp_sec) || 0, 0, durationSec);
  return {
    start_sec: clamp(timestamp - policy.before, 0, durationSec),
    end_sec: clamp(timestamp + policy.after, 0, durationSec),
  };
}

export function buildClipCandidates(events = [], durationSec = 0) {
  const safeDuration = Math.max(0, Number(durationSec) || 0);
  const sorted = events.map((event) => normalizeEvent(event, safeDuration)).sort((a, b) => a.timestamp_sec - b.timestamp_sec);
  const candidates = sorted.map((event) => {
    const window = createClipWindow(event, safeDuration);
    return {
      clip_id: `clip-${event.event_id}`,
      event_ids: [event.event_id],
      event_types: [event.label],
      label: event.label,
      confidence: event.confidence,
      score: event.confidence,
      start_sec: window.start_sec,
      end_sec: window.end_sec,
      duration_sec: Math.max(0, window.end_sec - window.start_sec),
      status: "ready",
      video_url: null,
    };
  });

  return candidates.reduce((merged, candidate) => {
    const previous = merged.at(-1);
    if (!previous || candidate.start_sec > previous.end_sec) {
      merged.push(candidate);
      return merged;
    }

    previous.end_sec = Math.max(previous.end_sec, candidate.end_sec);
    previous.duration_sec = previous.end_sec - previous.start_sec;
    previous.event_ids = [...new Set([...previous.event_ids, ...candidate.event_ids])];
    previous.event_types = [...new Set([...previous.event_types, ...candidate.event_types])];
    previous.label = previous.event_types.join(" + ");
    previous.confidence = Math.max(previous.confidence, candidate.confidence);
    previous.score = previous.confidence;
    previous.clip_id = `clip-${previous.event_ids.join("-")}`;
    return merged;
  }, []);
}

export function formatEventLabel(classId) {
  return EVENT_TYPES.find((event) => event.id === classId)?.label || classId.replaceAll("_", " ");
}
