import { test, expect } from "@playwright/test";
import { signIn } from "./helpers";

test("add a new product", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Products" }).click();
  await page.getByRole("link", { name: "New product" }).click();
  await page.getByLabel("Name").fill("Cold Brew Bottle");
  await page.getByLabel("SKU").fill("BTL-300");
  await page.getByLabel("Category").selectOption("Kitchen");
  await page.getByLabel("Price").fill("18");
  await page.getByLabel("Stock").fill("25");
  await page.getByRole("button", { name: "Save product" }).click();
  await expect(page.getByRole("heading", { name: "Cold Brew Bottle" })).toBeVisible();
});

test("adjust stock for a product", async ({ page }) => {
  await signIn(page);
  await page.goto("/products");
  await page.getByRole("link", { name: "Ceramic Mug" }).click();
  await page.getByLabel("Adjust stock").fill("30");
  await page.getByRole("button", { name: "Update stock" }).click();
  await expect(page.getByText("30")).toBeVisible();
});

test("price validation", async ({ page }) => {
  await signIn(page);
  await page.goto("/products/new");
  await page.getByRole("button", { name: "Save product" }).click();
  await expect(page.getByText("Price must be greater than 0")).toBeVisible();
});
