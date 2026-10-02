import type { ReactNode } from "react";

/**
 * Fades its children into place. Pure CSS (see `.reveal` in globals.css): a server
 * component with no JavaScript, so the content is always in the HTML and visible.
 */
export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <div className={`reveal ${className ?? ""}`} style={delay ? { animationDelay: `${delay}s` } : undefined}>
      {children}
    </div>
  );
}
