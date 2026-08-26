import { expect, test } from "@playwright/test";

test("staff RBAC redirects, signs in, and signs out", async ({ page }) => {
  await page.route("**/api/auth/login", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "demo-jwt",
        token_type: "bearer",
        expires_in: 28800,
        user: {
          id: "11111111-1111-1111-1111-111111111111",
          email: "agent@tokomate.local",
          full_name: "Demo Support Agent",
          role: "agent",
        },
      }),
    });
  });
  await page.route("**/api/auth/me", async (route) => {
    expect(route.request().headers().authorization).toBe("Bearer demo-jwt");
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        id: "11111111-1111-1111-1111-111111111111",
        email: "agent@tokomate.local",
        full_name: "Demo Support Agent",
        role: "agent",
      }),
    });
  });
  await page.route("**/api/dashboard/stats", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ active_ai: 1, ai_resolved: 2, escalated: 0 }),
    });
  });
  await page.route("**/api/escalations?*", async (route) => {
    await route.fulfill({ contentType: "application/json", body: "[]" });
  });

  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login$/);

  await page.getByRole("button", { name: "Use English" }).click();
  await page.getByRole("button", { name: "Sign in to dashboard" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Agent support center" })).toBeVisible();
  await expect(page.getByText("Demo Support Agent")).toBeVisible();

  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect(await page.evaluate(() => localStorage.getItem("tokomate_staff_access_token"))).toBeNull();
});
