import { expect, test } from "@playwright/test";

test.describe("Core go-live flows", () => {
  test("marketing -> pricing -> auth entry", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: "IP IPFlow" })).toBeVisible();

    await page.goto("/pricing");
    await expect(page.getByText("选择适合您的计划")).toBeVisible();

    await page.goto("/login");
    await expect(page.getByTestId("text-login-title")).toBeVisible();
  });

  test("dashboard route requires auth or renders shell", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/dashboard|\/login/);
  });
});
