import type { Metadata } from "next";
import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { ForecastCard, FormPills } from "@/app/components/Forecast";
import { Reveal } from "@/app/components/motion";
import { ScoutNote } from "@/app/components/ScoutNote";
import {
  getLeagueTable,
  getPredictions,
  getTeamMatches,
  getTeamPlayers,
  type Forecast,
  type ShotLeader,
  type TableRow,
  type TeamMatch,
} from "@/lib/api";
import { competitionColor, currentSeasonStartYear, seasonDisplay } from "@/lib/format";

function param(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export async function generateMetadata(props: PageProps<"/equipos/[team]">): Promise<Metadata> {
  const { team } = await props.params;
  return { title: `${decodeURIComponent(team)} · El Regista` };
}

const W = 720;
const H = 200;
const PAD = 24;

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

/** xG created (blue) and conceded (orange) match by match, as bars. */
function XgChart({ matches }: { matches: TeamMatch[] }) {
  if (matches.length === 0) return null;
  const max = Math.max(...matches.flatMap((m) => [m.xg_for, m.xg_against]), 1);
  const slot = (W - PAD * 2) / matches.length;
  const bar = Math.min(slot * 0.35, 16);
  const mid = H / 2;
  const scale = (value: number) => round((value / max) * (mid - 12));
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label="xG a favor y en contra por partido">
      <line x1={PAD} x2={W - PAD} y1={mid} y2={mid} stroke="rgba(22,23,27,0.15)" />
      {matches.map((match, index) => {
        const x = round(PAD + slot * index + slot / 2);
        const colour = match.result === "w" ? "#34d399" : match.result === "d" ? "#9ca3af" : "#fb7185";
        return (
          <g key={match.match_id}>
            <rect x={round(x - bar / 2)} y={round(mid - scale(match.xg_for))} width={round(bar)} height={scale(match.xg_for)} rx="3" fill="#2350d8" />
            <rect x={round(x - bar / 2)} y={mid} width={round(bar)} height={scale(match.xg_against)} rx="3" fill="#c93c17" opacity="0.85" />
            <circle cx={x} cy={H - 6} r="3" fill={colour} />
            <title>{`vs ${match.opponent} · ${match.goals_for}-${match.goals_against} · xG ${match.xg_for.toFixed(2)}-${match.xg_against.toFixed(2)}`}</title>
          </g>
        );
      })}
    </svg>
  );
}

function Stat({ value, label, tone }: { value: string; label: string; tone?: string }) {
  return (
    <div className="glass rounded-lg p-4">
      <span className={`block font-display text-3xl font-bold tabular-nums ${tone ?? ""}`}>{value}</span>
      <span className="text-xs text-muted">{label}</span>
    </div>
  );
}

export default async function TeamPage(props: PageProps<"/equipos/[team]">) {
  const { team: encoded } = await props.params;
  const team = decodeURIComponent(encoded);
  const searchParams = await props.searchParams;
  const league = param(searchParams.liga) ?? "La Liga";
  const season = param(searchParams.temporada) ?? String(currentSeasonStartYear());

  const [table, matches, players, forecasts] = await Promise.all([
    getLeagueTable(season, league).catch((): TableRow[] => []),
    getTeamMatches(team, season).catch((): TeamMatch[] => []),
    getTeamPlayers(team, season).catch((): ShotLeader[] => []),
    getPredictions(45, league).catch((): Forecast[] => []),
  ]);
  const row = table.find((entry) => entry.team === team);
  const upcoming = forecasts
    .filter((f) => f.home_team === team || f.away_team === team)
    .slice(0, 3);
  const played = row?.played || 1;
  const luck = row ? row.points - row.xpts : 0;
  const pressingRank = row?.ppda
    ? table.filter((r) => r.ppda !== null && (r.ppda ?? 0) < (row.ppda ?? 0)).length + 1
    : null;

  return (
    <div className="flex flex-col gap-10">
      <Reveal>
        <Link href={`/equipos?liga=${encodeURIComponent(league)}&temporada=${season}`} className="text-sm text-muted hover:text-ink">
          ← {league} {seasonDisplay(season)}
        </Link>
        <h1 className="mt-2 flex items-center gap-3 font-display text-5xl font-bold tracking-tight">
          <span className="h-3 w-3 rounded-full" style={{ background: competitionColor(league) }} />
          {team}
        </h1>
        {row && (
          <p className="mt-2 flex items-center gap-3 text-sm text-muted">
            {row.position}º en {league} · <FormPills form={row.form} size="md" />
          </p>
        )}
      </Reveal>

      {row && (
        <Reveal className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat value={`${row.points}`} label={`puntos (merece ${row.xpts.toFixed(1)})`} tone={luck >= 2 ? "text-brand-2" : luck <= -2 ? "text-rose-300" : ""} />
          <Stat value={(row.xg_for / played).toFixed(2)} label="xG a favor por partido" />
          <Stat value={(row.xg_against / played).toFixed(2)} label="xG en contra por partido" />
          <Stat value={row.ppda?.toFixed(1) ?? "—"} label={pressingRank ? `PPDA · ${pressingRank}º que más presiona` : "PPDA"} />
        </Reveal>
      )}

      {row && Math.abs(luck) >= 2 && (
        <p className="glass rounded-lg p-4 text-sm">
          <ScoutNote rotate={-2} className="text-base">
            {luck > 0 ? "ojo, puede venir bajón:" : "debería ir a más:"}
          </ScoutNote>{" "}
          lleva {Math.abs(luck).toFixed(1)} puntos {luck > 0 ? "más" : "menos"} de lo que merecen sus
          ocasiones. Esas rachas suelen corregirse con el tiempo.
        </p>
      )}

      {matches.length > 0 && (
        <Reveal>
          <section className="glass rounded-lg p-5">
            <h2 className="font-heading text-xl">Ocasiones partido a partido</h2>
            <p className="mb-2 text-xs text-muted">
              Arriba, xG creado; abajo, xG concedido. El punto indica el resultado (verde victoria, gris
              empate, rojo derrota).
            </p>
            <XgChart matches={matches} />
          </section>
        </Reveal>
      )}

      {upcoming.length > 0 && (
        <section className="flex flex-col gap-4">
          <h2 className="font-heading text-2xl">Próximos partidos</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {upcoming.map((forecast) => (
              <ForecastCard key={forecast.match_id} forecast={forecast} />
            ))}
          </div>
        </section>
      )}

      {players.length > 0 && (
        <section className="flex flex-col gap-4">
          <h2 className="font-heading text-2xl">Quién pone las ocasiones</h2>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {players.map((player) => (
              <Link
                key={player.player_id}
                href={`/players/${player.player_id}`}
                className="glass glass-hover flex items-center gap-3 rounded-lg p-3"
              >
                <Avatar name={player.name} photoUrl={player.photo_url} size={42} />
                <span className="flex-1 truncate font-semibold">{player.name}</span>
                <span className="text-right text-xs text-muted">
                  <strong className="font-heading text-base text-ink">{player.goals}</strong> goles
                  <br />
                  {player.value.toFixed(1)} xG · {player.shots} tiros
                </span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {matches.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="font-heading text-2xl">Resultados</h2>
          <ul className="glass divide-y divide-line/60 rounded-lg">
            {[...matches].reverse().map((match) => (
              <li key={match.match_id} className="grid grid-cols-[90px_1fr_auto_auto] items-center gap-3 px-4 py-2.5 text-sm">
                <span className="text-xs text-muted">{new Date(match.played_on).toLocaleDateString("es-ES", { day: "numeric", month: "short" })}</span>
                <span className="truncate">
                  {match.home ? "vs" : "en"} {match.opponent}
                </span>
                <span className="font-display font-bold tabular-nums">
                  {match.goals_for}-{match.goals_against}
                </span>
                <span className="w-24 text-right text-xs tabular-nums text-muted">
                  xG {match.xg_for.toFixed(1)}-{match.xg_against.toFixed(1)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
