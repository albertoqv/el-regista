import { expect, test, type Page } from "@playwright/test";

async function noHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => {
    window.scrollTo(10_000, 0);
    return window.scrollX;
  });
  expect(overflow, "la página no debe desplazarse en horizontal").toBe(0);
}

test("la portada enseña Scout y esconde los pronósticos", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("h1").first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Scout/ }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Pronósticos/ })).toHaveCount(0);
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
  await page.getByRole("link", { name: "Premier League", exact: true }).click();
  await expect(page).toHaveURL(/\/ranking\/premier-league\/goleadores/);
  await noHorizontalScroll(page);
});

test("los pronósticos siguen cargando por enlace, sin indexar", async ({ page }) => {
  await page.goto("/predicciones");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Próximos partidos");
  await expect(page.getByRole("link", { name: /juego responsable/i }).first()).toBeVisible();
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);
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

test("ninguna página clave da errores en consola (CSP incluida)", async ({ page }) => {
  test.setTimeout(120_000);
  const errors: string[] = [];
  // Vercel's analytics script only exists on Vercel, not on a local build.
  const local = (text: string) => text.includes("_vercel/insights");
  page.on("console", (message) => {
    const text = message.text();
    // Failed loads are checked below with their URL.
    if (message.type() === "error" && !local(text) && !text.startsWith("Failed to load resource")) {
      errors.push(text);
    }
  });
  page.on("response", (response) => {
    if (response.status() >= 400 && !local(response.url())) errors.push(`${response.status()} ${response.url()}`);
  });
  page.on("pageerror", (error) => errors.push(error.message));
  for (const path of ["/", "/predicciones", "/ranking/laliga/goleadores", "/gemelos", "/compare"]) {
    await page.goto(path, { waitUntil: "load" });
    await page.waitForTimeout(1_500);
  }
  await page.goto("/ranking/laliga/goleadores");
  await page.locator("ol li a").first().click();
  await expect(page).toHaveURL(/\/players\/\d+/);
  await page.waitForTimeout(1_500);
  expect(errors).toEqual([]);
});
