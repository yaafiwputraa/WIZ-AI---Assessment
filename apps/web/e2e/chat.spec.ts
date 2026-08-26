import { expect, test } from "@playwright/test";

test("customer can start a bilingual chat", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.route("**/api/chat", async (route) => {
    const request = route.request().postDataJSON();
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        conversation_id: "11111111-1111-1111-1111-111111111111",
        conversation_status: "ai_active",
        user_message: {
          id: "22222222-2222-2222-2222-222222222222",
          sender: "customer",
          content: request.message,
          created_at: new Date().toISOString(),
        },
        assistant_message: {
          id: "33333333-3333-3333-3333-333333333333",
          sender: "assistant",
          content: "Adidas Samba black size 42 has 3 pairs in stock for Rp1,499,000.",
          created_at: new Date().toISOString(),
        },
        tool_trace_identifiers: ["trace-1"],
        escalation: null,
      }),
    });
  });
  await page.goto("/chat");
  await page.getByRole("button", { name: "Use English" }).click();
  await page.getByLabel("Your name").fill("Budi");
  await page.getByRole("button", { name: "Start chatting" }).click();
  await page.getByPlaceholder("Type your question…").fill("Is Adidas Samba black size 42 in stock?");
  await page.getByRole("button", { name: "Send" }).click();
  await page.waitForTimeout(1000);
  expect(pageErrors).toEqual([]);
  await expect(page.getByText(/3 pairs in stock/)).toBeVisible();
});
