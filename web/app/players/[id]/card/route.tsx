import { ImageResponse } from "next/og";
import { SITE_HOST } from "@/lib/site";
import { LOGO_DARK, LOGO_RATIO, OG_COLORS, OG_FONTS } from "@/lib/og-brand";
import {
  getMarketValue,
  getPlayerPercentiles,
  getPlayerSeason,
  listPlayerSeasons,
  type PercentileReport,
} from "@/lib/api";
import {
  bigPhoto,
  competitionColor,
  formatAge,
  formatMarketValue,
  positionLabel,
  seasonDisplay,
  sortSeasonsByRecency,
} from "@/lib/format";
import { PROFILE_LABELS, percentileColor } from "@/lib/metrics";

const WIDTH = 1080;
const HEIGHT = 1350;

function strengths(report: PercentileReport | null) {
  if (!report) return [];
  return Object.entries(report.metrics)
    .sort((a, b) => b[1].percentile - a[1].percentile)
    .slice(0, 5)
    .map(([metric, value]) => ({ label: PROFILE_LABELS[metric] ?? metric, percentile: value.percentile }));
}

/** Shareable player card (Instagram portrait size) for the latest season. */
export async function GET(_request: Request, ctx: RouteContext<"/players/[id]/card">) {
  const { id } = await ctx.params;
  const playerId = Number(id);
  const seasons = sortSeasonsByRecency(await listPlayerSeasons(playerId).catch(() => []));
  const season = seasons[0];
  if (!season) return new Response("Not found", { status: 404 });

  const [player, value, report] = await Promise.all([
    getPlayerSeason(playerId, season),
    getMarketValue(playerId).catch(() => ({ current: null, history: [] })),
    getPlayerPercentiles(playerId, season).catch(() => null),
  ]);
  const accent = competitionColor(season.competition);
  const photo = bigPhoto(player.photo_url);
  const age = formatAge(player);
  const numbers = [
    { label: "Goles", value: String(player.goals) },
    { label: "Asist.", value: String(player.assists) },
    { label: "xG", value: player.expected_goals.toFixed(1) },
    { label: "xA", value: player.expected_assists.toFixed(1) },
    { label: "Minutos", value: String(player.minutes_played) },
  ];

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          background: OG_COLORS.slate,
          color: "#f7f6f2",
          padding: 64,
          fontFamily: "Regista",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={LOGO_DARK} height={46} width={Math.round(46 * LOGO_RATIO)} alt="" />
          <div
            style={{
              display: "flex",
              background: "#f2643a",
              color: "#16171b",
              padding: "8px 18px",
              fontSize: 24,
              fontWeight: 400,
              transform: "rotate(-3deg)",
              borderRadius: 4,
            }}
          >
            {`${season.competition} ${seasonDisplay(season.label)}`}
          </div>
        </div>

        <div style={{ display: "flex", marginTop: 40, gap: 40 }}>
          <div
            style={{
              display: "flex",
              width: 420,
              height: 546,
              borderRadius: 36,
              overflow: "hidden",
              background: "#0f1013",
            }}
          >
            {photo && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={photo} width={420} height={546} style={{ objectFit: "cover" }} alt="" />
            )}
          </div>
          <div style={{ display: "flex", flexDirection: "column", flex: 1, justifyContent: "flex-end" }}>
            <div style={{ display: "flex", fontSize: 26, color: accent, fontWeight: 700, textTransform: "uppercase", letterSpacing: 4 }}>
              {positionLabel(player.position)}
            </div>
            <div style={{ display: "flex", fontSize: 76, fontWeight: 400, lineHeight: 1, letterSpacing: -2, marginTop: 8 }}>
              {player.name}
            </div>
            <div style={{ display: "flex", fontSize: 28, color: "#a9acb3", marginTop: 16 }}>
              {[season.team, age ? `${age} años` : null].filter(Boolean).join(" · ")}
            </div>
            {value.current && (
              <div style={{ display: "flex", fontSize: 64, fontWeight: 400, color: "#5b8cff", marginTop: 24 }}>
                {formatMarketValue(value.current.amount_eur)}
              </div>
            )}
          </div>
        </div>

        <div style={{ display: "flex", gap: 16, marginTop: 44 }}>
          {numbers.map((number) => (
            <div
              key={number.label}
              style={{
                display: "flex",
                flexDirection: "column",
                flex: 1,
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 24,
                padding: "18px 20px",
              }}
            >
              <span style={{ fontSize: 52, fontWeight: 400 }}>{number.value}</span>
              <span style={{ fontSize: 22, color: "#a9acb3" }}>{number.label}</span>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 14, marginTop: 40 }}>
          {strengths(report).map((strength) => (
            <div key={strength.label} style={{ display: "flex", alignItems: "center", gap: 20 }}>
              <span style={{ width: 220, fontSize: 26, color: "#f7f6f2" }}>{strength.label}</span>
              <div style={{ display: "flex", flex: 1, height: 18, borderRadius: 9, background: "rgba(255,255,255,0.07)" }}>
                <div
                  style={{
                    width: `${Math.max(strength.percentile, 3)}%`,
                    height: 18,
                    borderRadius: 9,
                    background: percentileColor(strength.percentile),
                  }}
                />
              </div>
              <span style={{ width: 70, fontSize: 32, fontWeight: 400, color: percentileColor(strength.percentile), textAlign: "right" }}>
                {strength.percentile}
              </span>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", marginTop: "auto", justifyContent: "space-between", fontSize: 22, color: "#a9acb3" }}>
          <span>{report ? `Percentil vs ${report.peer_count} de su puesto en ${report.competition}` : ""}</span>
          <span>{SITE_HOST}</span>
        </div>
      </div>
    ),
    {
      width: WIDTH,
      height: HEIGHT,
      fonts: OG_FONTS,
      headers: { "Cache-Control": "public, max-age=3600, s-maxage=86400" },
    },
  );
}
