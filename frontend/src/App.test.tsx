import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("identifies the foundation status without claiming analytical results", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Indy Geospatial Accessibility Platform",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "No analytical results are available yet",
    );
    expect(
      screen.getByRole("heading", { level: 2, name: "Method note" }),
    ).toBeInTheDocument();
  });
});
