const FILL_COLOR = "#2a78d6";

export function SimilarityMeter({
  percentage,
  size = 128,
}: {
  percentage: number;
  size?: number;
}) {
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.min(Math.max(percentage, 0), 100) / 100);

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          fill="none"
          className="stroke-zinc-200 dark:stroke-zinc-800"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={FILL_COLOR}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-semibold">{percentage}%</span>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">parecido</span>
      </div>
    </div>
  );
}
