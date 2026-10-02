import { expect, test, type Page } from "@playwright/test";

async function noHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => {
    window.scrollTo(10_000, 0);
    return window.scrollX;
  });
  expect(overflow, "la página no debe desplazarse en horizontal").toBe(0);
}

test("la portada enseña los dos productos", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("h1").first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Scout/ }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Pronósticos/ }).first()).toBeVisible();
  await noHorizontalScroll(page);
});

test("buscar un jugador lleva a su ficha", async ({ page }) => {
  await page.goto("/buscar");
  await page.getByPlaceholder(/Busca cualquier jugador/).fill("Lamine");
  await page.getByRole("button", { name: /Lamine Yamal/ }).first().click();
  await expect(page).toHaveURL(/\/players\/\d+/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Lamine Yamal");
  await noHorizontalScroll(page);
});

test("los rankings tienen datos de la temporada", async ({ page }) => {
  await page.goto("/ranking/laliga/goleadores");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Goleadores de LaLiga");
  await expect(page.locator("ol li")).toHaveCount(50);
  await page.getByRole("link", { name: "Premier League" }).click();
  await expect(page).toHaveURL(/\/ranking\/premier-league\/goleadores/);
  await noHorizontalScroll(page);
});

test("los pronósticos cargan", async ({ page }) => {
  await page.goto("/predicciones");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Próximos partidos");
  await expect(page.getByRole("link", { name: /juego responsable/i }).first()).toBeVisible();
  await noHorizontalScroll(page);
});

test("el historial de aciertos carga", async ({ page }) => {
  await page.goto("/predicciones/historial");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await noHorizontalScroll(page);
});

test("una página que no existe devuelve 404", async ({ page }) => {
  const response = await page.goto("/esto-no-existe");
  expect(response?.status()).toBe(404);
});
