import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";
import { selectedFeatureProperties } from "./selection";

describe("App", () => {
  it("identifies the proximity-analysis status and limitations", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Indy Geospatial Accessibility Platform",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Loading local PostGIS analysis",
    );
    expect(
      screen.getByRole("heading", { level: 2, name: "How to read this" }),
    ).toBeInTheDocument();
  });
});

it("preserves per-feature score and detail properties for selection", () => {
  const properties = selectedFeatureProperties({
    properties: {
      geoid: "180970001001",
      total_accessibility_score: 72.5,
      transit_access_score: 50,
      service_access_score: 87.5,
      transit_stop_count: 4,
      service_categories: ["hospital", "library"],
      status_flags: [],
    },
  });
  expect(properties.total_accessibility_score).toBe(72.5);
  expect(properties.geoid).toBe("180970001001");
  expect(properties.service_categories).toEqual(["hospital", "library"]);
});
