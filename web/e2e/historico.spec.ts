import { expect, test } from "@playwright/test";

// Static history (no database): twins across eras, best seasons and a player's peak.

test("los gemelos de época buscan un jugador y enseñan a quién se parece", async ({ page }) => {
  await page.goto("/epocas");
  await page.getByPlaceholder(/Busca un jugador/).fill("Lionel Messi");
  await page.getByRole("link", { name: /Lionel Messi/ }).first().click();
  await expect(page).toHaveURL(/\/epocas\?j=\d+/);
  await expect(page.getByRole("heading", { level: 2 }).first()).toContainText("Lionel Messi");
  await expect(page.getByText("parecido").first()).toBeVisible();
});

test("las mejores temporadas listan 50 y cambian de métrica", async ({ page }) => {
  await page.goto("/mejores-temporadas");
  await expect(page.locator("ol li")).toHaveCount(50);
  await page.getByRole("link", { name: "Asistencias", exact: true }).click();
  await expect(page).toHaveURL(/metrica=asistencias/);
  await expect(page.locator("ol li")).toHaveCount(50);
});
