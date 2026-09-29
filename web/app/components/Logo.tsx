const BRAND_COLOR = "#2a78d6";

export function Logo({
  size = 28,
  withWordmark = true,
}: {
  size?: number;
  withWordmark?: boolean;
}) {
  return (
    <span className="inline-flex items-center gap-2">
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke={BRAND_COLOR}
        strokeWidth={1.75}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <circle cx="10.5" cy="10.5" r="6.5" />
        <circle cx="10.5" cy="10.5" r="3" />
        <circle cx="10.5" cy="10.5" r="0.75" fill={BRAND_COLOR} />
        <line x1="15.3" y1="15.3" x2="20.5" y2="20.5" />
      </svg>
      {withWordmark && (
        <span
          className="text-lg font-semibold tracking-tight"
          style={{ color: BRAND_COLOR }}
        >
          TalentScope
        </span>
      )}
    </span>
  );
}
