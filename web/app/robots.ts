import type { MetadataRoute } from "next";
import { SITE_URL as SITE } from "@/lib/site";

// Crawlers that train models or sell SEO data: they bring no visitors and every page
// they fetch is rendered on the server (Vercel Hobby paused the account in Nov 2026
// for CPU). Search engines and assistants fetching a page for a person stay allowed.
const BLOCKED_BOTS = [
  "GPTBot",
  "ClaudeBot",
  "anthropic-ai",
  "CCBot",
  "Google-Extended",
  "Applebot-Extended",
  "Bytespider",
  "meta-externalagent",
  "Amazonbot",
  "PetalBot",
  "AhrefsBot",
  "SemrushBot",
  "MJ12bot",
  "DotBot",
  "DataForSeoBot",
];

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: BLOCKED_BOTS, disallow: "/" },
      // Season pickers and comparisons add ?a=&b=&sc=... links: endless combinations
      // of the same pages (each one canonical without them).
      // The share cards keep theirs (/epocas/carta?a=&b=): the longer rule wins.
      { userAgent: "*", allow: ["/", "/epocas/carta"], disallow: ["/admin", "/api/", "/*?"] },
    ],
    sitemap: `${SITE}/sitemap.xml`,
  };
}
