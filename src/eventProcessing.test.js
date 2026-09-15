import { describe, expect, it } from "vitest";
import { buildClipCandidates, createClipWindow, filterAndSortEvents } from "./eventProcessing";

const events = [
  { event_id: "late", class_id: "shot", label: "Shot", timestamp_sec: 90, confidence: 0.4 },
  { event_id: "goal", class_id: "goal", label: "Goal", timestamp_sec: 20, confidence: 0.9 },
  { event_id: "foul", class_id: "foul", label: "Foul", timestamp_sec: 30, confidence: 0.8 },
];

describe("event processing", () => {
  it("filters by selected classes and confidence, then sorts by time", () => {
    const result = filterAndSortEvents(events, { selectedTypeIds: ["goal", "shot"], threshold: 0.5 });
    expect(result.map((event) => event.event_id)).toEqual(["goal"]);
  });

  it("clamps event windows to the video duration", () => {
    expect(createClipWindow({ class_id: "goal", timestamp_sec: 2 }, 100)).toEqual({ start_sec: 0, end_sec: 17 });
    expect(createClipWindow({ class_id: "shot", timestamp_sec: 99 }, 100)).toEqual({ start_sec: 91, end_sec: 100 });
  });

  it("merges overlapping windows and preserves contributing events", () => {
    const result = buildClipCandidates(
      [
        { event_id: "goal", class_id: "goal", label: "Goal", timestamp_sec: 20, confidence: 0.8 },
        { event_id: "shot", class_id: "shot", label: "Shot", timestamp_sec: 30, confidence: 0.9 },
      ],
      100,
    );
    expect(result).toHaveLength(1);
    expect(result[0].event_ids).toEqual(["goal", "shot"]);
    expect(result[0].event_types).toEqual(["Goal", "Shot"]);
    expect(result[0].start_sec).toBe(5);
    expect(result[0].end_sec).toBe(38);
  });

  it("returns an empty list for empty input", () => {
    expect(buildClipCandidates([], 100)).toEqual([]);
  });
});
