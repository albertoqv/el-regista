import type { Metadata } from "next";
import { CompareVerdict } from "@/app/components/CompareVerdict";
import { ComparePicker } from "@/app/components/ComparePicker";
import { DuelCard } from "@/app/components/DuelCard";
import { FaceOff } from "@/app/components/FaceOff";
import { HeadToHead } from "@/app/components/HeadToHead";
import { KeyMoments } from "@/app/components/KeyMoments";
import { MarketValueChart } from "@/app/components/MarketValueChart";
import { Reveal } from "@/app/components/motion";
import { PercentileLegend } from "@/app/components/PercentileBars";
import { RadarChart } from "@/app/components/RadarChart";
import {
  ApiError,
  comparePlayers,
  getMarketValue,
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
import { currentSeasonStartYear, seasonDisplay } from "@/lib/format";
import { RADAR_METRICS } from "@/lib/metrics";
import { CAREER, resolveSeason } from "@/lib/seasons";

function param(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function contextLabel(season: Season | null, team: string | null | undefined): string {
  if (!season) return "Carrera completa";
  return `${team ?? season.competition} · ${seasonDisplay(season.label)}`;
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

  const [summaryA, summaryB, seasonsA, seasonsB] = await Promise.all([
    idA ? getPlayer(idA).catch(() => null) : null,
    idB ? getPlayer(idB).catch(() => null) : null,
    idA ? listPlayerSeasons(idA).catch(() => [] as Season[]) : ([] as Season[]),
    idB ? listPlayerSeasons(idB).catch(() => [] as Season[]) : ([] as Season[]),
  ]);
  const seasonA = resolveSeason(seasonsA, param(searchParams.sac), param(searchParams.sal));
  const seasonB = resolveSeason(seasonsB, param(searchParams.sbc), param(searchParams.sbl));

  let content = null;
  let error: string | null = null;

  if (idA && idB && summaryA && summaryB) {
    try {
      const [comparison, playerA, playerB, valueA, valueB, percentilesA, percentilesB, shotsA, shotsB] =
        await Promise.all([
          comparePlayers(idA, idB, {
            seasonA: seasonA ?? undefined,
            seasonB: seasonB ?? undefined,
          }),
          seasonA ? getPlayerSeason(idA, seasonA) : getPlayer(idA),
          seasonB ? getPlayerSeason(idB, seasonB) : getPlayer(idB),
          getMarketValue(idA).catch(() => EMPTY_VALUE),
          getMarketValue(idB).catch(() => EMPTY_VALUE),
          seasonA ? getPlayerPercentiles(idA, seasonA).catch(() => null) : null,
          seasonB ? getPlayerPercentiles(idB, seasonB).catch(() => null) : null,
          getPlayerShots(idA, seasonA?.label).catch((): PlayerShot[] => []),
          getPlayerShots(idB, seasonB?.label).catch((): PlayerShot[] => []),
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
              context: contextLabel(seasonA, seasonA && seasonsA.find((s) => s.label === seasonA.label && s.competition === seasonA.competition)?.team),
              marketValue: content.valueA.current,
            }}
            b={{
              player: content.playerB,
              context: contextLabel(seasonB, seasonB && seasonsB.find((s) => s.label === seasonB.label && s.competition === seasonB.competition)?.team),
              marketValue: content.valueB.current,
            }}
            similarity={content.comparison.similarity_percentage}
          />

          <Reveal>
            <CompareVerdict playerA={content.playerA} playerB={content.playerB} />
          </Reveal>

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
                  axes={RADAR_METRICS}
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
            <HeadToHead playerA={content.playerA} playerB={content.playerB} />
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
