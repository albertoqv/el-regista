import { ImageResponse } from "next/og";
import { seasonDisplay } from "@/lib/format";
import { HISTORY_METRICS } from "@/lib/history";
import { LOGO_DARK, LOGO_RATIO, OG_COLORS, OG_FONTS } from "@/lib/og-brand";
import { loadProfiles, pickSeason, similarity, type Profile } from "@/lib/profiles";
import { SITE_HOST } from "@/lib/site";

const WIDTH = 1200;
const HEIGHT = 630;
const RADAR = 300;
const RADIUS = 125;
// Brighter than the web's tones: they sit on the dark card.
const COLOR_A = "#f2643a";
const COLOR_B = "#5b8cff";

function polygon(profile: Profile): string {
  return HISTORY_METRICS.map((key, index) => {
    const angle = (Math.PI * 2 * index) / HISTORY_METRICS.length - Math.PI / 2;
    const distance = (Math.max(profile.percentiles[key], 4) / 100) * RADIUS;
    return `${Math.round(RADAR / 2 + Math.cos(angle) * distance)},${Math.round(RADAR / 2 + Math.sin(angle) * distance)}`;
  }).join(" ");
}

function ring(ratio: number): string {
  return HISTORY_METRICS.map((_, index) => {
    const angle = (Math.PI * 2 * index) / HISTORY_METRICS.length - Math.PI / 2;
    return `${Math.round(RADAR / 2 + Math.cos(angle) * RADIUS * ratio)},${Math.round(RADAR / 2 + Math.sin(angle) * RADIUS * ratio)}`;
  }).join(" ");
}

function Side({ profile, color, align }: { profile: Profile; color: string; align: "flex-start" | "flex-end" }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, alignItems: align, textAlign: align === "flex-end" ? "right" : "left" }}>
      <div style={{ display: "flex", fontSize: 58, lineHeight: 1, color }}>{profile.name}</div>
      <div style={{ display: "flex", fontSize: 30, marginTop: 14, color: OG_COLORS.chalk }}>
        {`${profile.competition} ${seasonDisplay(String(profile.year))}`}
      </div>
      <div style={{ display: "flex", fontSize: 24, marginTop: 6, color: OG_COLORS.dim }}>{profile.team}</div>
    </div>
  );
}

/** Share image of two seasons across eras: `?a=2097:la-liga-2015&b=...`. */
export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const profiles = await loadProfiles();
  const a = pickSeason(params.get("a") ?? undefined, profiles)?.profile;
  const b = pickSeason(params.get("b") ?? undefined, profiles)?.profile;
  if (!a) return new Response("Not found", { status: 404 });

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          background: OG_COLORS.slate,
          color: OG_COLORS.chalk,
          padding: "48px 64px",
          fontFamily: "Regista",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={LOGO_DARK} height={40} width={Math.round(40 * LOGO_RATIO)} alt="" />
          <div style={{ display: "flex", fontSize: 30, color: OG_COLORS.dim }}>{b ? "Gemelos de época" : "Su temporada"}</div>
        </div>

        <div style={{ display: "flex", alignItems: "center", flex: 1, gap: 32 }}>
          <Side profile={a} color={COLOR_A} align="flex-start" />
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <svg width={RADAR} height={RADAR} viewBox={`0 0 ${RADAR} ${RADAR}`}>
              {[0.5, 1].map((ratio) => (
                <polygon key={ratio} points={ring(ratio)} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth={2} />
              ))}
              <polygon points={polygon(a)} fill="rgba(242,100,58,0.3)" stroke={COLOR_A} strokeWidth={4} />
              {b && <polygon points={polygon(b)} fill="rgba(91,140,255,0.3)" stroke={COLOR_B} strokeWidth={4} />}
            </svg>
            {b && <div style={{ display: "flex", fontSize: 76, marginTop: 8 }}>{`${similarity(a, b)}%`}</div>}
          </div>
          {b ? <Side profile={b} color={COLOR_B} align="flex-end" /> : <div style={{ display: "flex", flex: 1 }} />}
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 22, color: OG_COLORS.dim }}>
          <span>Percentiles de Understat frente a su puesto, liga y temporada</span>
          <span>{SITE_HOST}</span>
        </div>
      </div>
    ),
    {
      width: WIDTH,
      height: HEIGHT,
      fonts: OG_FONTS,
      headers: { "Cache-Control": "public, max-age=3600, s-maxage=604800" },
    },
  );
}
