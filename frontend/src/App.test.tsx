import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

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
