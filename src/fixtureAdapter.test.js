import { describe, expect, it } from "vitest";
import { runFixtureProcessing } from "./fixtureAdapter";

describe("fixture adapter", () => {
  it("produces deterministic local results without a network client", async () => {
    const progress = [];
    const result = await runFixtureProcessing({
      durationSec: 120,
      selectedTypeIds: ["goal"],
      threshold: 0.9,
      onProgress: (value) => progress.push(value),
    });

    expect(result.source).toBe("fixture");
    expect(result.events).toHaveLength(1);
    expect(result.events[0].class_id).toBe("goal");
    expect(result.clips).toHaveLength(1);
    expect(progress.at(-1)).toBe(100);
  });
});
