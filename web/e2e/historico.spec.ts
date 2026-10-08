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

test("el cara a cara histórico enfrenta dos temporadas de cualquier época", async ({ page }) => {
  await page.goto("/epocas/duelo");
  await page.getByPlaceholder("Primer jugador").fill("Lionel Messi");
  await page.getByRole("link", { name: /Lionel Messi/ }).first().click();
  await expect(page).toHaveURL(/a=\d+/);
  await page.getByPlaceholder("Segundo jugador").fill("Cristiano Ronaldo");
  await page.getByRole("link", { name: /Cristiano Ronaldo/ }).first().click();
  await expect(page).toHaveURL(/b=\d+/);
  await expect(page.getByText("de parecido en su forma de jugar")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Métrica a métrica" })).toBeVisible();
});

test("un jugador que no tenemos tiene su ficha histórica y su carta para compartir", async ({ page, request }) => {
  const [iniesta] = await (await request.get("/historico/buscar?q=iniesta")).json();
  await page.goto(`/historico/jugador/${iniesta.id}`);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Iniesta");
  await expect(page.getByRole("heading", { name: "Temporada a temporada" })).toBeVisible();
  const card = await request.get(`/epocas/carta?a=${iniesta.id}`);
  expect(card.headers()["content-type"]).toContain("image/png");
});
