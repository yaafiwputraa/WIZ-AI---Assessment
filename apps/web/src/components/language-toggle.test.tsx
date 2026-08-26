import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LanguageToggle } from "./language-toggle";

describe("LanguageToggle", () => {
  it("changes the selected locale", () => {
    const onChange = vi.fn();
    render(<LanguageToggle locale="id" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: "Use English" }));
    expect(onChange).toHaveBeenCalledWith("en");
  });
});

