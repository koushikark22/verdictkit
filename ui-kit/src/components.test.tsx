import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { VerdictView, statusTone } from "./components";
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

describe("statusTone", () => {
  it("never renders an indeterminate or conditional result as passing", () => {
    expect(statusTone("INDETERMINATE")).toBe("warn");
    expect(statusTone("CONDITIONAL")).toBe("warn");
    expect(statusTone("IMPOSSIBLE")).toBe("fail");
    expect(statusTone("CONSISTENT")).toBe("pass");
  });
});
