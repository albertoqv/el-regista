import type { MetadataRoute } from "next";

const SITE = process.env.VERCEL_PROJECT_PRODUCTION_URL
  ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
  : "http://localhost:3000";

const PAGES: { path: string; changeFrequency: "daily" | "weekly" | "monthly"; priority: number }[] = [
  { path: "", changeFrequency: "daily", priority: 1 },
  { path: "/predicciones", changeFrequency: "daily", priority: 0.9 },
  { path: "/gemelos", changeFrequency: "weekly", priority: 0.9 },
  { path: "/equipos", changeFrequency: "daily", priority: 0.8 },
  { path: "/explorar", changeFrequency: "weekly", priority: 0.7 },
  { path: "/compare", changeFrequency: "weekly", priority: 0.7 },
  { path: "/como-funciona", changeFrequency: "monthly", priority: 0.5 },
];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return PAGES.map((page) => ({
    url: `${SITE}${page.path}`,
    lastModified: now,
    changeFrequency: page.changeFrequency,
    priority: page.priority,
  }));
}
