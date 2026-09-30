export function Logo({
  size = 28,
  withWordmark = true,
}: {
  size?: number;
  withWordmark?: boolean;
}) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <span
        className="relative inline-flex items-center justify-center rounded-xl"
        style={{
          width: size + 10,
          height: size + 10,
          background:
            "linear-gradient(135deg, rgba(61,139,255,0.25), rgba(34,211,238,0.12))",
          boxShadow: "0 0 24px rgba(61,139,255,0.45), inset 0 0 0 1px rgba(255,255,255,0.12)",
        }}
      >
        <svg
          width={size}
          height={size}
          viewBox="0 0 24 24"
          fill="none"
          strokeWidth={1.75}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="logo-stroke" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#9cc3ff" />
              <stop offset="100%" stopColor="#22d3ee" />
            </linearGradient>
          </defs>
          <circle cx="10.5" cy="10.5" r="6.5" stroke="url(#logo-stroke)" />
          <circle cx="10.5" cy="10.5" r="3" stroke="url(#logo-stroke)" />
          <circle cx="10.5" cy="10.5" r="0.9" fill="#22d3ee" stroke="none" />
          <line x1="15.3" y1="15.3" x2="20.5" y2="20.5" stroke="url(#logo-stroke)" />
        </svg>
      </span>
      {withWordmark && (
        <span className="font-display text-lg font-bold tracking-tight">
          Talent<span className="text-gradient">Scope</span>
        </span>
      )}
    </span>
  );
}
