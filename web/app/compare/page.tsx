import { ComparePicker } from "@/app/components/ComparePicker";
import { IconValue } from "@/app/components/icons";
import { MarketValueChart } from "@/app/components/MarketValueChart";
import { PlayerCompareChart } from "@/app/components/PlayerCompareChart";
import { PlayerHeroCard } from "@/app/components/PlayerHeroCard";
import { SimilarityMeter } from "@/app/components/SimilarityMeter";
import {
  ApiError,
  comparePlayers,
  getMarketValue,
  getPlayer,
  getPlayerSeason,
  listPlayers,
  sortByRecency,
  type Comparison,
  type MarketValuePoint,
  type Player,
  type Season,
} from "@/lib/api";

function paramValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function seasonFromParams(
  competition: string | undefined,
  label: string | undefined,
): Season | null {
  return competition && label ? { competition, label } : null;
}

function seasonLabel(season: Season | null): string {
  return season ? `${season.competition} ${season.label}` : "Carrera";
}

export default async function ComparePage(props: PageProps<"/compare">) {
  const searchParams = await props.searchParams;
  const rawA = paramValue(searchParams.a);
  const rawB = paramValue(searchParams.b);
  const idA = rawA ? Number(rawA) : null;
  const idB = rawB ? Number(rawB) : null;
  const seasonA = seasonFromParams(
    paramValue(searchParams.sac),
    paramValue(searchParams.sal),
  );
  const seasonB = seasonFromParams(
    paramValue(searchParams.sbc),
    paramValue(searchParams.sbl),
  );

  let players: Player[] = [];
  try {
    players = sortByRecency(await listPlayers());
  } catch {
    players = [];
  }

  let result: Comparison | null = null;
  let playerA: Player | null = null;
  let playerB: Player | null = null;
  let marketValueA: MarketValuePoint | null = null;
  let marketValueB: MarketValuePoint | null = null;
  let historyA: MarketValuePoint[] = [];
  let historyB: MarketValuePoint[] = [];
  let error: string | null = null;

  if (idA && idB) {
    try {
      const [comparison, playerAResult, playerBResult, marketA, marketB] =
        await Promise.all([
          comparePlayers(idA, idB, {
            seasonA: seasonA ?? undefined,
            seasonB: seasonB ?? undefined,
          }),
          seasonA ? getPlayerSeason(idA, seasonA) : getPlayer(idA),
          seasonB ? getPlayerSeason(idB, seasonB) : getPlayer(idB),
          getMarketValue(idA).catch(() => ({ current: null, history: [] })),
          getMarketValue(idB).catch(() => ({ current: null, history: [] })),
        ]);
      result = comparison;
      playerA = playerAResult;
      playerB = playerBResult;
      marketValueA = marketA.current;
      marketValueB = marketB.current;
      historyA = marketA.history;
      historyB = marketB.history;
    } catch (thrown) {
      error =
        thrown instanceof ApiError && thrown.status === 404
          ? "Alguno de los dos jugadores no existe para la temporada elegida."
          : "No se ha podido comparar a los jugadores.";
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">
          Comparar jugadores
        </h1>
        <ComparePicker
          players={players}
          defaultA={idA}
          defaultB={idB}
          defaultSeasonA={seasonA}
          defaultSeasonB={seasonB}
        />
      </section>

      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {result && playerA && playerB && (
        <>
          <section className="flex flex-col items-center gap-6 rounded-md border border-zinc-200 p-6 sm:flex-row dark:border-zinc-800">
            <PlayerHeroCard
              player={playerA}
              seasonLabel={seasonLabel(seasonA)}
              currentMarketValue={marketValueA}
            />
            <SimilarityMeter percentage={result.similarity_percentage} />
            <PlayerHeroCard
              player={playerB}
              seasonLabel={seasonLabel(seasonB)}
              currentMarketValue={marketValueB}
            />
          </section>

          <PlayerCompareChart playerA={playerA} playerB={playerB} />

          {(historyA.length > 0 || historyB.length > 0) && (
            <section className="flex flex-col gap-3">
              <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tight">
                <IconValue size={18} />
                Valor de mercado
              </h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <MarketValueChart history={historyA} />
                <MarketValueChart history={historyB} />
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
