import type { ReactNode } from "react";

/** Hand-drawn arrow, a little wobbly on purpose. */
export function HandArrow({
  className = "",
  direction = "down-left",
}: {
  className?: string;
  direction?: "down-left" | "down-right" | "right";
}) {
  const paths = {
    "down-left": "M58 6 C 52 22, 38 34, 12 44 M12 44 L 24 46 M12 44 L 18 33",
    "down-right": "M6 6 C 12 22, 26 34, 52 44 M52 44 L 40 46 M52 44 L 46 33",
    right: "M4 26 C 18 18, 36 18, 58 24 M58 24 L 47 17 M58 24 L 48 32",
  };
  return (
    <svg
      viewBox="0 0 64 50"
      className={`h-10 w-12 ${className}`}
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[direction]} />
    </svg>
  );
}

/** A scout's handwritten margin note. */
export function ScoutNote({
  children,
  className = "",
  rotate = -3,
}: {
  children: ReactNode;
  className?: string;
  rotate?: number;
}) {
  return (
    <span
      className={`font-hand text-xl leading-tight text-[#ffd76a] ${className}`}
      style={{ transform: `rotate(${rotate}deg)`, display: "inline-block" }}
    >
      {children}
    </span>
  );
}

/** Slightly crooked paper sticker, like the ones on a scout's folder. */
export function Sticker({
  children,
  tone = "yellow",
  rotate = -4,
  className = "",
}: {
  children: ReactNode;
  tone?: "yellow" | "green" | "red" | "white";
  rotate?: number;
  className?: string;
}) {
  const tones = {
    yellow: "bg-[#ffd76a] text-[#2a1d00]",
    green: "bg-[#7ef0b0] text-[#062414]",
    red: "bg-[#ff7a6b] text-[#2b0500]",
    white: "bg-[#f4efe4] text-[#1b1b1b]",
  };
  return (
    <span
      className={`sticker inline-block px-2.5 py-1 font-display text-[11px] font-black uppercase tracking-wider ${tones[tone]} ${className}`}
      style={{ transform: `rotate(${rotate}deg)` }}
    >
      {children}
    </span>
  );
}

/** Marker-pen highlight behind a word. */
export function Marker({ children, color = "#3d8bff" }: { children: ReactNode; color?: string }) {
  return (
    <span className="relative inline-block whitespace-nowrap">
      <svg
        viewBox="0 0 200 20"
        preserveAspectRatio="none"
        className="absolute -bottom-1 left-[-3%] h-[0.45em] w-[106%]"
        aria-hidden="true"
      >
        <path
          d="M2 12 C 40 6, 90 16, 140 9 S 190 8, 198 11"
          stroke={color}
          strokeWidth="7"
          strokeLinecap="round"
          fill="none"
          opacity="0.85"
          className="marker-stroke"
        />
      </svg>
      <span className="relative">{children}</span>
    </span>
  );
}
