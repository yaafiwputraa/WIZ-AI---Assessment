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

test("customer must verify an order before seeing delivery details", async ({ page }) => {
  let requestCount = 0;
  await page.route("**/api/chat", async (route) => {
    requestCount += 1;
    const request = route.request().postDataJSON();
    if (requestCount === 1) {
      expect(request.order_verification_code).toBeUndefined();
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
            content: "Enter the order verification code to continue.",
            created_at: new Date().toISOString(),
          },
          tool_trace_identifiers: ["trace-verify"],
          escalation: null,
          order_verification_required: true,
          order_verified: false,
          order_id: "ORD-192",
        }),
      });
      return;
    }

    expect(request.order_verification_code).toBe("TOKO192");
    expect(request.message).not.toContain("TOKO192");
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        conversation_id: "11111111-1111-1111-1111-111111111111",
        conversation_status: "ai_active",
        user_message: {
          id: "44444444-4444-4444-4444-444444444444",
          sender: "customer",
          content: request.message,
          created_at: new Date().toISOString(),
        },
        assistant_message: {
          id: "55555555-5555-5555-5555-555555555555",
          sender: "assistant",
          content: "Order ORD-192 has shipped with JNE. Tracking number JNE123456.",
          created_at: new Date().toISOString(),
        },
        tool_trace_identifiers: ["trace-order"],
        escalation: null,
        order_verification_required: false,
        order_verified: true,
        order_id: "ORD-192",
      }),
    });
  });

  await page.goto("/chat");
  await page.getByRole("button", { name: "Use English" }).click();
  await page.getByLabel("Your name").fill("Budi");
  await page.getByRole("button", { name: "Start chatting" }).click();
  await page.getByPlaceholder("Type your question…").fill("Where is my order ORD-192?");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByRole("heading", { name: "Verify your order" })).toBeVisible();
  await page.getByLabel("Verification code").fill("TOKO192");
  await page.getByRole("button", { name: "Verify and check order" }).click();

  await expect(page.getByText("Order verified: ORD-192")).toBeVisible();
  await expect(page.getByText(/JNE123456/)).toBeVisible();
  expect(requestCount).toBe(2);
});
