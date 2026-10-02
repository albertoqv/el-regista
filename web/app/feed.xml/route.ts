import { kickoffDate } from "@/app/components/Forecast";
import { getPredictions, type Forecast } from "@/lib/api";
import { SITE_URL } from "@/lib/site";

// Rebuilt every hour, like the sitemap.
export const revalidate = 3600;

function escape(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

const pct = (value: number) => `${Math.round(value * 100)}%`;

function item(forecast: Forecast): string {
  const kickoff = kickoffDate(forecast.kickoff);
  const when = kickoff.toLocaleString("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/Madrid",
  });
  const title = `${forecast.home_team} - ${forecast.away_team}`;
  const summary =
    `${forecast.competition}, ${when}. ${forecast.home_team} ${pct(forecast.home_win)}, ` +
    `empate ${pct(forecast.draw)}, ${forecast.away_team} ${pct(forecast.away_win)}. ` +
    `Más de 2,5 goles ${pct(forecast.over_2_5)}; marcan los dos ${pct(forecast.both_teams_score)}.`;
  const link = `${SITE_URL}/predicciones/${forecast.match_id}`;
  return [
    "<item>",
    `<title>${escape(title)}</title>`,
    `<link>${link}</link>`,
    `<guid isPermaLink="true">${link}</guid>`,
    `<category>${escape(forecast.competition)}</category>`,
    `<description>${escape(summary)}</description>`,
    "</item>",
  ].join("");
}

/** Upcoming matches with the model's probabilities: numbers only, no written previews. */
export async function GET() {
  const forecasts = await getPredictions(14).catch((): Forecast[] => []);
  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
    "<channel>",
    "<title>El Regista · Próximos partidos</title>",
    `<link>${SITE_URL}/predicciones</link>`,
    `<atom:link href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />`,
    "<description>Probabilidades de los próximos partidos de las cinco grandes ligas.</description>",
    "<language>es-es</language>",
    `<lastBuildDate>${new Date().toUTCString()}</lastBuildDate>`,
    ...forecasts.map(item),
    "</channel>",
    "</rss>",
  ].join("\n");
  return new Response(xml, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
}
