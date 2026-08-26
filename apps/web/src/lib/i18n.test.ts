import { describe, expect, it } from "vitest";

import { formatDate, t } from "./i18n";

describe("bilingual copy", () => {
  it("returns Indonesian and English chat labels", () => {
    expect(t("id").chat).toBe("Chat pelanggan");
    expect(t("en").chat).toBe("Customer chat");
  });

  it("formats a valid localized date", () => {
    expect(formatDate("2026-08-26T09:00:00Z", "en")).toContain("Aug");
  });
});

