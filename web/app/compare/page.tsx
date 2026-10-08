import type { Metadata } from "next";
import { CompareVerdict } from "@/app/components/CompareVerdict";
import { ComparePicker } from "@/app/components/ComparePicker";
import { DuelCard } from "@/app/components/DuelCard";
import { FaceOff } from "@/app/components/FaceOff";
import { HeadToHead } from "@/app/components/HeadToHead";
import { KeyMoments } from "@/app/components/KeyMoments";
import { MarketValueChart } from "@/app/components/MarketValueChart";
import { Reveal } from "@/app/components/Reveal";
import { PercentileLegend } from "@/app/components/PercentileBars";
import { RadarChart } from "@/app/components/RadarChart";
import {
  ApiError,
  type CompetitionLine,
  type Player,
  comparePlayers,
  getMarketValue,
  getPlayerCompetitions,
  getPlayer,
  getPlayerPercentiles,
  getPlayerShots,
  getPlayerSeason,
  listPlayerSeasons,
  listSeasonLeaders,
  type MarketValueHistory,
  type PercentileReport,
  type PlayerShot,
  type Season,
} from "@/lib/api";
import { ageInSeason, currentSeasonStartYear, seasonDisplay, valueAtSeason } from "@/lib/format";
import { HISTORY_METRICS, HISTORY_PREFIX, historyPercentiles, historyPlayer, historySeason, type HistoryRow } from "@/lib/history";
import { RADAR_METRICS } from "@/lib/metrics";
import { ALL_COMPETITIONS, CAREER, clubSeasons, playerInClubSeason, resolveSeason } from "@/lib/seasons";

function param(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function contextLabel(season: Season | null, team: string | null | undefined): string {
  if (!season) return "Carrera completa";
  if (season.competition === ALL_COMPETITIONS) {
    return `${season.team ?? "Club"} · ${seasonDisplay(season.label)}, todas las competiciones`;
  }
  if (season.competition.startsWith(HISTORY_PREFIX)) {
    return `${team ?? season.competition.slice(HISTORY_PREFIX.length)} · ${seasonDisplay(season.label)}`;
  }
  return `${team ?? season.competition} · ${seasonDisplay(season.label)}`;
}

/**
 * The season asked for; without one, the latest league season, or (for a player
 * without league seasons here, like Messi) his latest whole club season.
 */
function pickSeason(
  seasons: Season[],
  lines: CompetitionLine[],
  competition: string | undefined,
  label: string | undefined,
): Season | null {
  if (competition?.startsWith(HISTORY_PREFIX) && label) return { competition, label };
  if (competition === ALL_COMPETITIONS && label) {
    return clubSeasons(lines).find((season) => season.label === label) ?? { competition, label };
  }
  if (!competition && label !== CAREER && seasons.length === 0) return clubSeasons(lines)[0] ?? null;
  return resolveSeason(seasons, competition, label);
}

type DuelSide = { player: Player; games: number | null };

/** Games in a season: from the history row, or the club's competition lines. */
function gamesIn(season: Season | null, lines: CompetitionLine[], row: HistoryRow | null): number | null {
  if (row) return row.games ?? null;
  if (!season) return null;
  const club = lines.filter((line) => line.kind !== "national" && line.season_label === season.label);
  const own = season.competition === ALL_COMPETITIONS ? club : club.filter((line) => line.competition === season.competition);
  return own.length ? own.reduce((total, line) => total + line.appearances, 0) : null;
}

/** Side by side, what both seasons have: the basics, and xG/xA when both carry them. */
function BasicDuel({ a, b, detailed, note }: { a: DuelSide; b: DuelSide; detailed: boolean; note: string }) {
  const per90 = (player: Player) =>
    player.minutes_played ? ((player.goals + player.assists) * 90) / player.minutes_played : 0;
  const rows: [string, (side: DuelSide) => number | null, number][] = [
    ["Partidos", (side) => side.games, 0],
    ["Goles", (side) => side.player.goals, 0],
    ["Asistencias", (side) => side.player.assists, 0],
    ["Goles + asist. por 90", (side) => per90(side.player), 2],
    ...(detailed
      ? ([
          ["xG", (side) => side.player.expected_goals, 1],
          ["xA", (side) => side.player.expected_assists, 1],
          ["Tiros", (side) => side.player.shots, 0],
          ["Pases clave", (side) => side.player.key_passes, 0],
        ] as [string, (side: DuelSide) => number, number][])
      : []),
    ["Minutos", (side) => side.player.minutes_played, 0],
    ["Amarillas", (side) => side.player.yellow_cards, 0],
  ];
  const show = (value: number | null, decimals: number) =>
    value === null
      ? "—"
      : value.toLocaleString("es-ES", { maximumFractionDigits: decimals, minimumFractionDigits: decimals });
  return (
    <section className="glass flex flex-col gap-3 rounded-lg p-6">
      <div className="text-center">
        <h2 className="font-heading text-2xl tracking-tight">Números de la temporada</h2>
        <p className="text-sm text-muted">{note}</p>
      </div>
      <table className="w-full table-fixed text-sm">
        <tbody>
          {rows.map(([label, value, decimals]) => {
            const left = value(a);
            const right = value(b);
            const leftWins = left !== null && right !== null && left > right;
            const rightWins = left !== null && right !== null && right > left;
            return (
              <tr key={label} className="border-t border-line/60">
                <td className={`py-2 text-left tabular-nums ${leftWins ? "font-bold text-side-a" : ""}`}>
                  {show(left, decimals)}
                </td>
                <td className="text-center text-muted">{label}</td>
                <td className={`text-right tabular-nums ${rightWins ? "font-bold text-side-b" : ""}`}>
                  {show(right, decimals)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

const EMPTY_VALUE: MarketValueHistory = { current: null, history: [] };

async function suggestions() {
  const leaders = await listSeasonLeaders(currentSeasonStartYear(), {
    metric: "goals",
    limit: 6,
  }).catch(() => []);
  const pairs = [];
  for (let i = 0; i + 1 < leaders.length && pairs.length < 3; i += 2) {
    pairs.push({ a: leaders[i], b: leaders[i + 1] });
  }
  return pairs;
}

export async function generateMetadata(props: PageProps<"/compare">): Promise<Metadata> {
  const searchParams = await props.searchParams;
  const ids = [param(searchParams.a), param(searchParams.b)].map((id) => Number(id) || null);
  const players = await Promise.all(ids.map((id) => (id ? getPlayer(id).catch(() => null) : null)));
  if (players[0] && players[1]) {
    return {
      title: `${players[0].name} vs ${players[1].name} · El Regista`,
      description: `Cara a cara con datos reales: ${players[0].name} contra ${players[1].name}.`,
    };
  }
  return {
    title: "Comparar jugadores · El Regista",
    description: "Enfrenta a dos futbolistas con radar, percentiles, tiros y valor de mercado.",
  };
}

export default async function ComparePage(props: PageProps<"/compare">) {
  const searchParams = await props.searchParams;
  const idA = Number(param(searchParams.a)) || null;
  const idB = Number(param(searchParams.b)) || null;

  const [summaryA, summaryB, seasonsA, seasonsB, linesA, linesB] = await Promise.all([
    idA ? getPlayer(idA).catch(() => null) : null,
    idB ? getPlayer(idB).catch(() => null) : null,
    idA ? listPlayerSeasons(idA).catch(() => [] as Season[]) : ([] as Season[]),
    idB ? listPlayerSeasons(idB).catch(() => [] as Season[]) : ([] as Season[]),
    idA ? getPlayerCompetitions(idA).catch((): CompetitionLine[] => []) : [],
    idB ? getPlayerCompetitions(idB).catch((): CompetitionLine[] => []) : [],
  ]);
  const seasonA = pickSeason(seasonsA, linesA, param(searchParams.sac), param(searchParams.sal));
  const seasonB = pickSeason(seasonsB, linesB, param(searchParams.sbc), param(searchParams.sbl));
  // A whole club season (every competition) has only the basic numbers: no radar,
  // no shots, no style similarity.
  const wholeA = seasonA?.competition === ALL_COMPETITIONS;
  const wholeB = seasonB?.competition === ALL_COMPETITIONS;
  // A big five season from 2014-2023: Understat's numbers from the static history.
  const histA = Boolean(seasonA?.competition.startsWith(HISTORY_PREFIX));
  const histB = Boolean(seasonB?.competition.startsWith(HISTORY_PREFIX));
  const basic = wholeA || wholeB || histA || histB;
  const [historyA, historyB] = await Promise.all([
    histA && seasonA && summaryA
      ? historySeason(seasonA.competition.slice(HISTORY_PREFIX.length), Number(seasonA.label), summaryA.name)
      : null,
    histB && seasonB && summaryB
      ? historySeason(seasonB.competition.slice(HISTORY_PREFIX.length), Number(seasonB.label), summaryB.name)
      : null,
  ]);

  let content = null;
  let error: string | null = null;

  if ((histA && !historyA) || (histB && !historyB)) {
    error = "No encontramos esa temporada en el histórico para uno de los dos jugadores.";
  } else if (idA && idB && summaryA && summaryB) {
    try {
      const [comparison, playerA, playerB, valueA, valueB, percentilesA, percentilesB, shotsA, shotsB] =
        await Promise.all([
          basic
            ? null
            : comparePlayers(idA, idB, {
                seasonA: seasonA ?? undefined,
                seasonB: seasonB ?? undefined,
              }),
          historyA
            ? historyPlayer(summaryA, historyA.row)
            : wholeA && seasonA
            ? playerInClubSeason(summaryA, linesA, seasonA.label)
            : seasonA
              ? getPlayerSeason(idA, seasonA)
              : getPlayer(idA),
          historyB
            ? historyPlayer(summaryB, historyB.row)
            : wholeB && seasonB
            ? playerInClubSeason(summaryB, linesB, seasonB.label)
            : seasonB
              ? getPlayerSeason(idB, seasonB)
              : getPlayer(idB),
          getMarketValue(idA).catch(() => EMPTY_VALUE),
          getMarketValue(idB).catch(() => EMPTY_VALUE),
          historyA
            ? historyPercentiles(historyA.row, historyA.peers)
            : seasonA && !wholeA && !histA
              ? getPlayerPercentiles(idA, seasonA).catch(() => null)
              : null,
          historyB
            ? historyPercentiles(historyB.row, historyB.peers)
            : seasonB && !wholeB && !histB
              ? getPlayerPercentiles(idB, seasonB).catch(() => null)
              : null,
          wholeA || histA ? [] : getPlayerShots(idA, seasonA?.label).catch((): PlayerShot[] => []),
          wholeB || histB ? [] : getPlayerShots(idB, seasonB?.label).catch((): PlayerShot[] => []),
        ]);
      content = {
        comparison,
        playerA,
        playerB,
        valueA,
        valueB,
        percentilesA: percentilesA as PercentileReport | null,
        percentilesB: percentilesB as PercentileReport | null,
        shotsA,
        shotsB,
      };
    } catch (thrown) {
      error =
        thrown instanceof ApiError && thrown.status === 404
          ? "Alguno de los dos jugadores no tiene datos para la temporada elegida."
          : "No se ha podido comparar a los jugadores. Inténtalo de nuevo.";
    }
  }

  const pairs = content ? [] : await suggestions();
  const toValues = (report: PercentileReport | null) =>
    report
      ? Object.fromEntries(Object.entries(report.metrics).map(([key, value]) => [key, value.percentile]))
      : {};

  return (
    <div className="flex flex-col gap-10">
      <section className="flex flex-col gap-5">
        <Reveal>
          <p className="text-xs font-semibold text-side-b">Cara a cara</p>
          <h1 className="font-display text-4xl font-bold tracking-tight sm:text-5xl">
            Enfrenta a <span className="text-side-a">dos</span> jugadores
          </h1>
          <p className="mt-1 text-sm text-muted">Dos jugadores, cara a cara.</p>
        </Reveal>
        <ComparePicker
          defaultA={summaryA}
          defaultB={summaryB}
          seasonA={param(searchParams.sac) ? seasonA : null}
          seasonB={param(searchParams.sbc) ? seasonB : null}
          careerA={param(searchParams.sal) === CAREER}
          careerB={param(searchParams.sbl) === CAREER}
        />
      </section>

      {error && <p className="glass rounded-lg p-5 text-sm text-red-300">{error}</p>}

      {content && (
        <>
          <FaceOff
            a={{
              player: content.playerA,
              context: contextLabel(seasonA, historyA?.row.team ?? (seasonA && seasonsA.find((s) => s.label === seasonA.label && s.competition === seasonA.competition)?.team)),
              marketValue: content.valueA.current,
              then: seasonA
                ? {
                    label: seasonA.label,
                    value: valueAtSeason(content.valueA.history, seasonA.label),
                    age: ageInSeason(content.playerA, seasonA.label),
                  }
                : null,
            }}
            b={{
              player: content.playerB,
              context: contextLabel(seasonB, historyB?.row.team ?? (seasonB && seasonsB.find((s) => s.label === seasonB.label && s.competition === seasonB.competition)?.team)),
              marketValue: content.valueB.current,
              then: seasonB
                ? {
                    label: seasonB.label,
                    value: valueAtSeason(content.valueB.history, seasonB.label),
                    age: ageInSeason(content.playerB, seasonB.label),
                  }
                : null,
            }}
            similarity={content.comparison?.similarity_percentage ?? null}
          />

          {!basic && (
            <Reveal>
              <CompareVerdict playerA={content.playerA} playerB={content.playerB} />
            </Reveal>
          )}

          {(content.percentilesA || content.percentilesB) && (
            <Reveal>
              <section className="glass flex flex-col gap-4 rounded-lg p-6">
                <div className="text-center">
                  <h2 className="font-heading text-2xl tracking-tight">Radar de percentiles</h2>
                  <p className="mx-auto max-w-2xl text-sm text-muted">
                    Cada uno frente a los jugadores de su puesto en su liga. Cuanto más hacia fuera,
                    mejor que el resto (100 = el mejor).
                  </p>
                </div>
                <RadarChart
                  axes={histA || histB ? HISTORY_METRICS : RADAR_METRICS}
                  series={[
                    { name: content.playerA.name, color: "#2350d8", values: toValues(content.percentilesA) },
                    { name: content.playerB.name, color: "#c93c17", values: toValues(content.percentilesB) },
                  ]}
                />
                <div className="flex flex-col items-center gap-2">
                  <div className="flex gap-5 text-sm font-semibold">
                    <span className="text-side-a">● {content.playerA.name}</span>
                    <span className="text-side-b">● {content.playerB.name}</span>
                  </div>
                  <PercentileLegend />
                </div>
              </section>
            </Reveal>
          )}

          <Reveal>
            {basic ? (
              <BasicDuel
                a={{ player: content.playerA, games: gamesIn(seasonA, linesA, historyA?.row ?? null) }}
                b={{ player: content.playerB, games: gamesIn(seasonB, linesB, historyB?.row ?? null) }}
                detailed={!wholeA && !wholeB}
                note={
                  wholeA || wholeB
                    ? "Lo que tienen todas las competiciones: liga, Europa y copas sumadas."
                    : "Liga. Las temporadas de 2014 a 2023 vienen de Understat: sin pases, regates ni defensa."
                }
              />
            ) : (
              <HeadToHead playerA={content.playerA} playerB={content.playerB} />
            )}
          </Reveal>

          <Reveal>
            <KeyMoments
              nameA={content.playerA.name}
              nameB={content.playerB.name}
              shotsA={content.shotsA}
              shotsB={content.shotsB}
            />
          </Reveal>

          {(content.valueA.history.length > 0 || content.valueB.history.length > 0) && (
            <Reveal>
              <MarketValueChart
                series={[
                  { name: content.playerA.name, color: "#2350d8", history: content.valueA.history },
                  { name: content.playerB.name, color: "#c93c17", history: content.valueB.history },
                ]}
              />
            </Reveal>
          )}
        </>
      )}

      {!content && pairs.length > 0 && (
        <section className="flex flex-col gap-4">
          <h2 className="font-heading text-xl tracking-tight">
            ¿Sin ideas? Prueba con estos duelos
          </h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {pairs.map((pair, index) => (
              <Reveal key={`${pair.a.player_id}-${pair.b.player_id}`} delay={index * 0.08}>
                <DuelCard title="Goleadores de la temporada" a={pair.a} b={pair.b} />
              </Reveal>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
