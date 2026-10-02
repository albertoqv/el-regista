import { expect, test } from "@playwright/test";

// What search engines and feed readers see: one run is enough.
test.skip(({ isMobile }) => isMobile, "no depende del dispositivo");

test("el sitemap lista jugadores, equipos y partidos", async ({ request }) => {
  const body = await (await request.get("/sitemap.xml")).text();
  const urls = body.match(/<loc>/g) ?? [];
  expect(urls.length).toBeGreaterThan(300);
  expect(body).toContain("/players/");
  expect(body).toContain("/equipos/");
  expect(body).toContain("/ranking/laliga/goleadores");
});

test("el feed RSS es XML válido", async ({ request }) => {
  const response = await request.get("/feed.xml");
  expect(response.headers()["content-type"]).toContain("application/rss+xml");
  const body = await response.text();
  expect(body).toMatch(/^<\?xml/);
  expect(body).toContain("</rss>");
});

test("la ficha de jugador lleva datos estructurados", async ({ page }) => {
  await page.goto("/ranking/laliga/goleadores");
  await page.locator("ol li a").first().click();
  await expect(page).toHaveURL(/\/players\/\d+/);
  const jsonLd = await page.locator('script[type="application/ld+json"]').first().textContent();
  expect(JSON.parse(jsonLd ?? "{}")["@type"]).toBe("Person");
});

test("robots.txt apunta al sitemap", async ({ request }) => {
  const body = await (await request.get("/robots.txt")).text();
  expect(body).toContain("Sitemap:");
});
