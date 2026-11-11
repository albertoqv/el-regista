/** Public address of the web, used in share images, sitemap and metadata. */
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://elregista.onrender.com";

/** The address without the protocol, as printed on share images. */
export const SITE_HOST = SITE_URL.replace(/^https?:\/\//, "");
