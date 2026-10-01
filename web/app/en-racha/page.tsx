import type { Metadata } from "next";
import { PageHeader } from "@/app/components/PageHeader";
import { PHOTOS } from "@/lib/photos";
import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { ShareCard } from "@/app/components/ShareCard";
import { getHotPlayers, type HotMetric, type HotPlayer } from "@/lib/api";
import { COMPETITIONS, competitionColor } from "@/lib/format";

export const metadata: Metadata = {
  title: "En racha · El Regista",
  description: "Los jugadores más en forma de las 5 grandes ligas en las últimas semanas.",
  openGraph: { images: ["/en-racha/card"] },
  twitter: { card: "summary_large_image", images: ["/en-racha/card"] },
};

const METRICS: { key: HotMetric; label: string; note: string }[] = [
  { key: "goals_assists", label: "Goles + asistencias", note: "los que más deciden" },
  { key: "goals", label: "Goleadores", note: "puro gol" },
  { key: "threat", label: "Peligro (xG + xA)", note: "lo que merecen, no la suerte" },
  { key: "form", label: "Por encima de su media", note: "los que se han encendido" },
];

const DAYS = [14, 30, 60];

function param(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? "";
}

function headline(player: HotPlayer, metric: HotMetric): { value: string; unit: string } {
  if (metric === "goals") return { value: String(player.goals), unit: "goles" };
  if (metric === "threat") return { value: (player.xg + player.xa).toFixed(1), unit: "xG + xA" };
  if (metric === "form") {
    const gain = player.per90 - (player.before_per90 ?? 0);
    return { value: `+${gain.toFixed(2)}`, unit: "G+A/90 vs antes" };
  }
  return { value: String(player.goals + player.assists), unit: "G + A" };
}

function href(params: Record<string, string>): string {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value));
  const text = query.toString();
  return `/en-racha${text ? `?${text}` : ""}`;
}

function PlayerLink({ player, children, className }: { player: HotPlayer; children: React.ReactNode; className?: string }) {
  return player.player_id ? (
    <Link href={`/players/${player.player_id}`} className={className}>
      {children}
    </Link>
  ) : (
    <div className={className}>{children}</div>
  );
}

export default async function HotPage(props: PageProps<"/en-racha">) {
  const searchParams = await props.searchParams;
  const metric = (METRICS.find((m) => m.key === param(searchParams.metric))?.key ?? "goals_assists") as HotMetric;
  const competition = (COMPETITIONS as readonly string[]).includes(param(searchParams.liga)) ? param(searchParams.liga) : "";
  const days = DAYS.includes(Number(param(searchParams.dias))) ? Number(param(searchParams.dias)) : 30;
  const board = await getHotPlayers({ metric, competition: competition || undefined, days, limit: 20 }).catch(() => null);
  const current = { metric, liga: competition, dias: String(days) };
  const [first, second, third, ...rest] = board?.players ?? [];
  const podium = [second, first, third].filter(Boolean) as HotPlayer[];

  return (
    <div className="flex flex-col gap-8">
      <PageHeader photo={PHOTOS.en_racha.src} title="En racha">Los más en forma de las 5 grandes ligas.</PageHeader>

      <div className="flex flex-col gap-3">
        <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0">
          {METRICS.map((entry) => (
            <Link
              key={entry.key}
              href={href({ ...current, metric: entry.key })}
              className={`shrink-0 rounded-lg px-4 py-2 transition ${entry.key === metric ? "bg-white text-bg" : "glass glass-hover"}`}
            >
              <span className="block text-sm font-semibold">{entry.label}</span>
            </Link>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="no-scrollbar -mx-4 flex gap-1.5 overflow-x-auto px-4 sm:mx-0 sm:px-0">
            {["", ...COMPETITIONS].map((league) => (
              <Link
                key={league || "all"}
                href={href({ ...current, liga: league })}
                className={`shrink-0 rounded-full px-3 py-1.5 font-medium ${league === competition ? "bg-white/15 text-ink" : "text-muted hover:text-ink"}`}
              >
                {league || "Todas"}
              </Link>
            ))}
          </div>
          <div className="ml-auto flex gap-1.5">
            {DAYS.map((value) => (
              <Link
                key={value}
                href={href({ ...current, dias: String(value) })}
                className={`rounded-full px-3 py-1.5 font-medium ${value === days ? "bg-white/15 text-ink" : "text-muted hover:text-ink"}`}
              >
                {value} días
              </Link>
            ))}
          </div>
        </div>
      </div>

      {!board || board.players.length === 0 ? (
        <p className="glass rounded-lg p-8 text-center text-muted">
          {board ? "Todavía no hay suficientes partidos en este periodo." : "No hemos podido cargar los datos ahora mismo."}
        </p>
      ) : (
        <>
          <section className="grid grid-cols-3 items-end gap-2 sm:gap-4">
            {podium.map((player) => {
              const rank = board.players.indexOf(player) + 1;
              const main = headline(player, metric);
              return (
                <PlayerLink
                  key={player.understat_player_id}
                  player={player}
                  className={`group relative block ${rank === 1 ? "" : "mt-8 sm:mt-12"}`}
                >
                  <PlayerPortrait
                    name={player.name}
                    photoUrl={player.photo_url}
                    accent={rank === 1 ? "#f2c230" : "#7cc0ff"}
                    rounded="rounded-lg sm:rounded-lg"
                    className="aspect-[3/4] transition duration-500 group-hover:-translate-y-1"
                  />
                  <span className="absolute left-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-black/70 font-display text-sm font-bold sm:h-9 sm:w-9 sm:text-lg">
                    {rank}
                  </span>
                  <div className="absolute inset-x-0 bottom-0 p-2 sm:p-4">
                    <span className="block truncate text-xs font-bold sm:text-base">{player.name}</span>
                    <span className="block truncate text-[10px] text-ink/70 sm:text-xs">{player.team}</span>
                    <span className="font-display text-xl font-bold text-[#f2c230] sm:text-3xl">{main.value}</span>
                    <span className="ml-1 text-[10px] text-ink/70 sm:text-xs">{main.unit}</span>
                  </div>
                </PlayerLink>
              );
            })}
          </section>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-muted">
              Del {new Date(`${board.window_start}T12:00:00Z`).toLocaleDateString("es-ES", { day: "numeric", month: "long" })} al{" "}
              {new Date(`${board.window_end}T12:00:00Z`).toLocaleDateString("es-ES", { day: "numeric", month: "long" })} · datos de Understat
            </p>
            <ShareCard
              name="en-racha"
              imageUrl={`/en-racha/card?${new URLSearchParams({ metric, dias: String(days), ...(competition ? { liga: competition } : {}) }).toString()}`}
              shareText="Los jugadores más en forma ahora mismo, en El Regista"
              label="Compartir ranking"
            />
          </div>

          {rest.length > 0 ? (
            <ol className="glass flex flex-col rounded-lg p-2 sm:p-3" start={4}>
              {rest.map((player, index) => {
                const main = headline(player, metric);
                return (
                  <li key={player.understat_player_id}>
                    <PlayerLink player={player} className="flex items-center gap-3 rounded-lg px-2 py-2.5 transition hover:bg-white/[0.04] sm:px-3">
                      <span className="w-6 shrink-0 text-center font-display font-bold text-muted">{index + 4}</span>
                      <Avatar name={player.name} photoUrl={player.photo_url} size={40} />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-semibold">{player.name}</span>
                        <span className="flex items-center gap-1.5 truncate text-xs text-muted">
                          <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: competitionColor(player.competition) }} />
                          {player.team} · {player.matches} partidos · {player.goals} G · {player.assists} A
                          <span className="hidden sm:inline"> · xG {player.xg.toFixed(1)} · xA {player.xa.toFixed(1)}</span>
                        </span>
                      </span>
                      <span className="shrink-0 text-right">
                        <span className="block font-display text-xl font-bold tabular-nums text-[#f2c230]">{main.value}</span>
                        <span className="block text-[10px] text-muted">{main.unit}</span>
                      </span>
                    </PlayerLink>
                  </li>
                );
              })}
            </ol>
          ) : null}
        </>
      )}
    </div>
  );
}
