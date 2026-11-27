import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EquityChart, VerdictView, statusTone } from "./components";
import synthetic from "../../api/examples/outcome_synthetic_reel.json";
import completed from "../../api/examples/outcome_completed_quote.json";
import blocked from "../../api/examples/outcome_blocked_reel_rights.json";
import type { OutcomeResponse } from "./types";

// api/examples are the contract's schema-valid placeholders (not results); used here only
// to check rendering rules.
describe("VerdictView", () => {
  it("shows the demonstration notice and no confidence class on synthetic outcomes", () => {
    render(<VerdictView outcome={synthetic as unknown as OutcomeResponse} />);
    expect(screen.getAllByTestId("demo-notice")).toHaveLength(2);
    expect(screen.getByTestId("headline").textContent).toContain("IMPOSSIBLE");
    expect(screen.getByTestId("headline").textContent).toContain("confidence none");
  });

  it("marks the point of failure and keeps integrity wording out of the verdict", () => {
    render(<VerdictView outcome={completed as unknown as OutcomeResponse} />);
    expect(screen.getByTestId("finding-amount_financed").textContent).toContain("point of failure");
    expect(screen.queryByTestId("demo-notice")).toBeNull();
  });

  it("renders blockers and no headline for BLOCKED", () => {
    render(<VerdictView outcome={blocked as unknown as OutcomeResponse} />);
    expect(screen.getByTestId("blockers").textContent).toContain("EVIDENCE_RIGHTS_UNVERIFIED");
    expect(screen.getByTestId("headline").textContent).toContain("NO VERDICT");
  });
});

describe("EquityChart", () => {
  // A test input shaped like the engine's EQUITY_SERIES record; the values are not a result.
  const record = {
    recordId: "r1", findingId: null, recordRole: "ILLUSTRATIVE", recordKind: "EQUITY_SERIES", note: "Illustrative series.",
    payload: { equity: ["10000.00000000", "9500.50000000", "4953.51000000"], point: { fee_bps_per_side: "0" } },
  };
  it("labels start and end from the engine's decimal strings; the end label is clear of the series, the start label has a halo", () => {
    render(<EquityChart record={record} />);
    const labels = [...document.querySelectorAll("svg text")].filter((t) => /^(start|end) /.test(t.textContent ?? ""));
    expect(labels.map((t) => t.textContent)).toEqual(["start 10000.00", "end 4953.51"]);
    const [start, end] = labels;
    // Where the line crosses the start label it must stay readable.
    expect(start.getAttribute("paint-order")).toBe("stroke");
    expect(start.getAttribute("stroke")).toBe("#ffffff");
    // The series stops at the end marker, so a label to the right of it can never be struck through by the line.
    const marker = document.querySelector("svg circle")!;
    expect(Number(end.getAttribute("x"))).toBeGreaterThan(Number(marker.getAttribute("cx")));
    expect(end.getAttribute("text-anchor")).toBe("start");
    expect(screen.getByTestId("equity-chart").textContent).toContain("ILLUSTRATIVE");
  });
});
describe("statusTone", () => {
  it("never renders an indeterminate or conditional result as passing", () => {
    expect(statusTone("INDETERMINATE")).toBe("warn");
    expect(statusTone("CONDITIONAL")).toBe("warn");
    expect(statusTone("IMPOSSIBLE")).toBe("fail");
    expect(statusTone("CONSISTENT")).toBe("pass");
  });
});
