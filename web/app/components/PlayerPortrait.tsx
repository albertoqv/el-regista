"use client";

import { useState } from "react";
import { bigPhoto } from "@/lib/format";

/** Generic player silhouette used when there is no photo yet. */
function Silhouette({ color }: { color: string }) {
  const id = `sil-${color.replace(/[^a-z0-9]/gi, "")}`;
  return (
    <svg viewBox="0 0 120 150" className="h-full w-full" aria-hidden="true">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.55" />
          <stop offset="100%" stopColor={color} stopOpacity="0.05" />
        </linearGradient>
      </defs>
      <circle cx="60" cy="48" r="22" fill={`url(#${id})`} />
      <path
        d="M18 150c2-34 18-56 42-56s40 22 42 56z"
        fill={`url(#${id})`}
      />
    </svg>
  );
}

/**
 * Large trading-card style portrait. The photo fades into the card at the
 * bottom so names and numbers can sit on top of it.
 */
export function PlayerPortrait({
  name,
  photoUrl,
  accent = "#c93c17",
  mirrored = false,
  className = "",
  rounded = "rounded-lg",
  focus = "center top",
  priority = false,
}: {
  name: string;
  photoUrl: string | null | undefined;
  accent?: string;
  mirrored?: boolean;
  className?: string;
  rounded?: string;
  /** CSS object-position: landscape crops need to aim lower to keep the face. */
  focus?: string;
  /** The main picture of the page: fetch it first. */
  priority?: boolean;
}) {
  // Try the sharp portrait first, then the original one, then the silhouette.
  const sources = [bigPhoto(photoUrl), photoUrl].filter(
    (url, index, all): url is string => !!url && all.indexOf(url) === index,
  );
  const [attempt, setAttempt] = useState(0);
  const source = sources[attempt] ?? null;
  const failed = source === null;
  const next = () => setAttempt((current) => current + 1);

  return (
    <div
      className={`relative overflow-hidden ${rounded} ${className}`}
      style={{
        background: `radial-gradient(120% 90% at 50% 0%, ${accent}33, transparent 60%), linear-gradient(180deg, #e9e7e1, #ffffff)`,
        boxShadow: "0 0 0 1px rgba(22,23,27,0.08)",
      }}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "repeating-linear-gradient(135deg, rgba(22,23,27,0.03) 0 2px, transparent 2px 12px)",
        }}
      />
      {!failed ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          key={source}
          src={source}
          alt={name}
          onError={next}
          loading={priority ? "eager" : "lazy"}
          fetchPriority={priority ? "high" : "auto"}
          ref={(node) => {
            // The error may fire before hydration, when onError is not attached yet.
            if (node && node.complete && node.naturalWidth === 0) next();
          }}
          className="absolute inset-0 h-full w-full object-cover"
          style={{
            objectPosition: focus,
            transform: mirrored ? "scaleX(-1)" : undefined,
            maskImage: "linear-gradient(180deg, black 55%, transparent 98%)",
            WebkitMaskImage: "linear-gradient(180deg, black 55%, transparent 98%)",
          }}
        />
      ) : (
        <div className="absolute inset-x-0 bottom-0 top-[8%]">
          <Silhouette color={accent} />
        </div>
      )}
      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 h-1/3"
        style={{ background: "linear-gradient(0deg, #ffffffee, transparent)" }}
      />
    </div>
  );
}
