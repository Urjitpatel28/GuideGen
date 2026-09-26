import { test, expect } from "@playwright/test";
import { signIn } from "./helpers";

test("create an order for an existing customer", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Orders" }).click();
  await page.getByRole("link", { name: "New order" }).click();
  await page.getByLabel("Customer").selectOption({ label: "Contoso Bakery" });
  await page.getByLabel("Product").selectOption({ index: 1 });
  await page.getByLabel("Quantity").fill("2");
  await page.getByRole("button", { name: "Create order" }).click();
  await expect(page.getByRole("heading", { name: /Order O\d+/ })).toBeVisible();
});

test("quantity must be greater than zero", async ({ page }) => {
  await signIn(page);
  await page.goto("/orders/new");
  await page.getByLabel("Customer").selectOption({ index: 1 });
  await page.getByLabel("Product").selectOption({ index: 1 });
  await page.getByLabel("Quantity").fill("0");
  await page.getByRole("button", { name: "Create order" }).click();
  await expect(page.getByText("Quantity must be greater than 0")).toBeVisible();
});

test("mark an order as shipped", async ({ page }) => {
  await signIn(page);
  await page.goto("/orders");
  await page.getByRole("link", { name: "O1003" }).click();
  await page.getByRole("button", { name: "Mark as shipped" }).click();
  await expect(page.getByText("Shipped").first()).toBeVisible();
});
