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
        viewBox="0 0 32 32"
        fill="none"
        aria-hidden="true"
      >
        <circle cx="14" cy="14" r="10" stroke={BRAND_COLOR} strokeWidth="3" />
        <path
          d="M14 8.5 L16 12.5 L20.5 13 L17 16 L18 20.5 L14 18.2 L10 20.5 L11 16 L7.5 13 L12 12.5 Z"
          fill={BRAND_COLOR}
        />
        <line
          x1="21.5"
          y1="21.5"
          x2="28"
          y2="28"
          stroke={BRAND_COLOR}
          strokeWidth="3.5"
          strokeLinecap="round"
        />
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
