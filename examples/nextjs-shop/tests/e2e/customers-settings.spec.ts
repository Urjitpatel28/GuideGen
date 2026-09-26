import { test, expect } from "@playwright/test";
import { signIn } from "./helpers";

test("add a customer", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Customers" }).click();
  await page.getByRole("link", { name: "New customer" }).click();
  await page.getByLabel("Name").fill("Tailspin Toys");
  await page.getByLabel("Email").fill("buyer@tailspin.example");
  await page.getByRole("button", { name: "Save customer" }).click();
  await expect(page.getByRole("cell", { name: "Tailspin Toys" })).toBeVisible();
});

test("change store settings", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Settings" }).click();
  await page.getByLabel("Low-stock threshold").fill("10");
  await page.getByLabel("Currency").selectOption("EUR");
  await page.getByRole("button", { name: "Save settings" }).click();
  await expect(page.getByText("Settings saved.")).toBeVisible();
});

test("sign out", async ({ page }) => {
  await signIn(page);
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Sign in to Acme Shop" })).toBeVisible();
});
