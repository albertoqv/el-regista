import { ImageResponse } from "next/og";
import { SITE_HOST } from "@/lib/site";
import { LOGO_DARK, LOGO_RATIO, OG_COLORS, OG_FONTS } from "@/lib/og-brand";
import { getHotPlayers, type HotMetric } from "@/lib/api";
import { bigPhoto } from "@/lib/format";

const WIDTH = 1080;
const HEIGHT = 1350;

const TITLES: Record<HotMetric, string> = {
  goals_assists: "Goles + asistencias",
  goals: "Goleadores",
  threat: "Peligro (xG + xA)",
  form: "Por encima de su media",
};

/** Shareable "on fire" ranking (Instagram portrait size). */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const metric = (Object.keys(TITLES).includes(url.searchParams.get("metric") ?? "")
    ? url.searchParams.get("metric")
    : "goals_assists") as HotMetric;
  const days = Number(url.searchParams.get("dias")) || 30;
  const competition = url.searchParams.get("liga") || undefined;
  const board = await getHotPlayers({ metric, days, competition, limit: 5 }).catch(() => null);
  const players = board?.players ?? [];

  function value(index: number): string {
    const player = players[index];
    if (metric === "goals") return `${player.goals} G`;
    if (metric === "threat") return (player.xg + player.xa).toFixed(1);
    if (metric === "form") return `+${(player.per90 - (player.before_per90 ?? 0)).toFixed(2)}`;
    return `${player.goals + player.assists} G+A`;
  }

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
            {`Últimos ${days} días`}
          </div>
        </div>
        <div style={{ display: "flex", fontSize: 96, fontWeight: 400, letterSpacing: -3, marginTop: 36 }}>En racha</div>
        <div style={{ display: "flex", fontSize: 34, color: "#a9acb3", marginTop: 4 }}>
          {`${TITLES[metric]} · ${competition ?? "5 grandes ligas"}`}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 18, marginTop: 44 }}>
          {players.map((player, index) => {
            const photo = bigPhoto(player.photo_url);
            return (
              <div
                key={player.understat_player_id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 28,
                  background: index === 0 ? "rgba(242,100,58,0.12)" : "rgba(255,255,255,0.05)",
                  border: `1px solid ${index === 0 ? "rgba(242,100,58,0.5)" : "rgba(255,255,255,0.1)"}`,
                  borderRadius: 28,
                  padding: "16px 28px",
                }}
              >
                <span style={{ display: "flex", width: 56, fontSize: 52, fontWeight: 400, color: index === 0 ? "#f2643a" : "#a9acb3" }}>
                  {String(index + 1)}
                </span>
                <div style={{ display: "flex", width: 112, height: 112, borderRadius: 56, overflow: "hidden", background: "#0f1013" }}>
                  {photo && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={photo} width={112} height={112} style={{ objectFit: "cover", objectPosition: "center top" }} alt="" />
                  )}
                </div>
                <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
                  <span style={{ fontSize: 42, fontWeight: 400 }}>{player.name}</span>
                  <span style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 24, color: "#a9acb3" }}>
                    {`${player.team} · ${player.matches} partidos`}
                  </span>
                </div>
                <span style={{ fontSize: 50, fontWeight: 400, color: "#f2643a" }}>{value(index)}</span>
              </div>
            );
          })}
        </div>

        <div style={{ display: "flex", marginTop: "auto", justifyContent: "space-between", fontSize: 22, color: "#a9acb3" }}>
          <span>Datos: Understat · mínimo 180 minutos</span>
          <span>{`${SITE_HOST}/en-racha`}</span>
        </div>
      </div>
    ),
    {
      width: WIDTH,
      height: HEIGHT,
      fonts: OG_FONTS,
      headers: { "Cache-Control": "public, max-age=3600, s-maxage=21600" },
    },
  );
}
