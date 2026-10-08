import type { Metadata } from "next";

// Pronósticos is hidden: its pages still work by link, but stay out of search engines.
export const metadata: Metadata = { robots: { index: false, follow: true } };

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
