import { Page } from "@playwright/test";

export async function signIn(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(process.env.GUIDEGEN_USER ?? "demo@shop.test");
  await page.getByLabel("Password").fill(process.env.GUIDEGEN_PASSWORD ?? "demo1234");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL("/");
}
