import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AppShell } from "./shell";

const VAR = "--vk-topbar-h";
const rect = (height: number) => ({ height, width: 0, top: 0, left: 0, right: 0, bottom: height, x: 0, y: 0, toJSON: () => ({}) }) as DOMRect;

describe("AppShell sticky top bar", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    document.documentElement.style.removeProperty(VAR);
  });

  it("publishes the bar's measured height and follows it when the bar wraps onto a second row", () => {
    let height = 56.2;
    vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(() => rect(height));
    const observers: Array<() => void> = [];
    vi.stubGlobal("ResizeObserver", class {
      constructor(callback: () => void) { observers.push(callback); }
      observe() { return undefined; }
      disconnect() { return undefined; }
    });
    const view = render(<AppShell active="home" health={null} error={null} loading={false}><main id="main" /></AppShell>);
    // theme.css uses this value as the page's scroll-padding-top, so a scrolled-to result clears the bar.
    expect(document.documentElement.style.getPropertyValue(VAR)).toBe("57px");
    height = 126.4;
    observers.forEach((callback) => callback());
    expect(document.documentElement.style.getPropertyValue(VAR)).toBe("127px");
    view.unmount();
  });

  it("still renders where ResizeObserver does not exist", () => {
    vi.stubGlobal("ResizeObserver", undefined);
    render(<AppShell active="verify" health={null} error={null} loading={false}><main id="main" /></AppShell>);
    expect(screen.getByRole("navigation", { name: "VerdictKit applications" })).toBeTruthy();
  });
});
