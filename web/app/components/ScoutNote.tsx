import type { ReactNode } from "react";

/*
 * The old hand-written notes and arrows are gone: El Regista keeps the page quiet.
 * These components stay so existing markup keeps compiling; notes render nothing.
 */

export function HandArrow(props: { className?: string; direction?: "down-left" | "down-right" | "right" }) {
  void props;
  return null;
}

export function ScoutNote(props: { children: ReactNode; className?: string; rotate?: number }) {
  void props;
  return null;
}

/** A flat label in the display face, like the "EL" tag of the logo. */
export function Sticker({
  children,
  tone = "yellow",
  className = "",
}: {
  children: ReactNode;
  tone?: "yellow" | "green" | "red" | "white";
  rotate?: number;
  className?: string;
}) {
  const tones = {
    yellow: "bg-brand text-bg",
    green: "bg-grass text-bg",
    red: "bg-side-b text-bg",
    white: "bg-ink text-bg",
  };
  return (
    <span className={`sticker inline-block px-2 py-0.5 font-heading text-sm ${tones[tone]} ${className}`}>
      {children}
    </span>
  );
}

/** Plain emphasis: the word keeps its colour, no marker scribble. */
export function Marker({ children }: { children: ReactNode; color?: string }) {
  return <span>{children}</span>;
}
