import { ImageResponse } from "next/og";
import { getHotPlayers, type HotMetric } from "@/lib/api";
import { bigPhoto, competitionColor } from "@/lib/format";

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
          background: "radial-gradient(circle at 50% 0%, #ff6b3d55, #070a14 55%)",
          color: "#eef2ff",
          padding: 64,
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", fontSize: 34, fontWeight: 800, letterSpacing: -1 }}>
            Talent<span style={{ color: "#22d3ee" }}>Scope</span>
          </div>
          <div
            style={{
              display: "flex",
              background: "#ffd76a",
              color: "#2a1d00",
              padding: "8px 18px",
              fontSize: 24,
              fontWeight: 900,
              transform: "rotate(-3deg)",
              borderRadius: 4,
            }}
          >
            {`Últimos ${days} días`}
          </div>
        </div>
        <div style={{ display: "flex", fontSize: 96, fontWeight: 800, letterSpacing: -3, marginTop: 36 }}>En racha</div>
        <div style={{ display: "flex", fontSize: 34, color: "#aab3c7", marginTop: 4 }}>
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
                  background: index === 0 ? "rgba(255,215,106,0.12)" : "rgba(255,255,255,0.05)",
                  border: `1px solid ${index === 0 ? "rgba(255,215,106,0.5)" : "rgba(255,255,255,0.1)"}`,
                  borderRadius: 28,
                  padding: "16px 28px",
                }}
              >
                <span style={{ display: "flex", width: 56, fontSize: 52, fontWeight: 800, color: index === 0 ? "#ffd76a" : "#8b93a7" }}>
                  {String(index + 1)}
                </span>
                <div style={{ display: "flex", width: 112, height: 112, borderRadius: 56, overflow: "hidden", background: "#0d1426" }}>
                  {photo && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={photo} width={112} height={112} style={{ objectFit: "cover", objectPosition: "center top" }} alt="" />
                  )}
                </div>
                <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
                  <span style={{ fontSize: 42, fontWeight: 800 }}>{player.name}</span>
                  <span style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 24, color: "#aab3c7" }}>
                    <span style={{ display: "flex", width: 12, height: 12, borderRadius: 6, background: competitionColor(player.competition) }} />
                    {`${player.team} · ${player.matches} partidos`}
                  </span>
                </div>
                <span style={{ fontSize: 50, fontWeight: 800, color: "#ffd76a" }}>{value(index)}</span>
              </div>
            );
          })}
        </div>

        <div style={{ display: "flex", marginTop: "auto", justifyContent: "space-between", fontSize: 22, color: "#8b93a7" }}>
          <span>Datos: Understat · mínimo 180 minutos</span>
          <span>web-seven-tan-39.vercel.app/en-racha</span>
        </div>
      </div>
    ),
    {
      width: WIDTH,
      height: HEIGHT,
      headers: { "Cache-Control": "public, max-age=3600, s-maxage=21600" },
    },
  );
}
