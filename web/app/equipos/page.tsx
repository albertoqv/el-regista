import type { Metadata } from "next";
import Link from "next/link";
import { FormPills } from "@/app/components/Forecast";
import { Reveal } from "@/app/components/motion";
import { ScoutNote } from "@/app/components/ScoutNote";
import { getLeagueTable, type TableRow } from "@/lib/api";
import { COMPETITIONS, competitionColor, currentSeasonStartYear, seasonDisplay } from "@/lib/format";

export const metadata: Metadata = {
  title: "Equipos · TalentScope",
  description: "Clasificación real frente a la merecida (xPts), xG, presión y forma de cada equipo.",
};

function param(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function signed(value: number, decimals = 1): string {
  const text = value.toFixed(decimals).replace(".", ",");
  return value > 0 ? `+${text}` : text;
}

export default async function TeamsPage(props: PageProps<"/equipos">) {
  const searchParams = await props.searchParams;
  const league = param(searchParams.liga) ?? "La Liga";
  const season = param(searchParams.temporada) ?? String(currentSeasonStartYear());
  const rows = await getLeagueTable(season, league).catch((): TableRow[] => []);
  const pressing = rows.filter((r) => r.ppda !== null).sort((a, b) => (a.ppda ?? 0) - (b.ppda ?? 0));
  const luckiest = [...rows].sort((a, b) => b.points - b.xpts - (a.points - a.xpts));
  const seasons = [0, 1, 2].map((offset) => String(currentSeasonStartYear() - offset));

  return (
    <div className="flex flex-col gap-8">
      <Reveal>
        <ScoutNote rotate={-2}>la tabla que no miente</ScoutNote>
        <h1 className="font-display text-4xl font-bold tracking-tight sm:text-5xl">Equipos</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          La clasificación de siempre junto a la que cada equipo <em>merece</em> por sus ocasiones
          (puntos esperados, xPts), cuánto presiona y cómo llega.
        </p>
      </Reveal>

      <div className="flex flex-col gap-3">
        <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0">
          {COMPETITIONS.map((option) => {
            const active = league === option;
            const color = competitionColor(option);
            return (
              <Link
                key={option}
                href={`/equipos?liga=${encodeURIComponent(option)}&temporada=${season}`}
                className="flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium"
                style={{
                  borderColor: active ? color : "rgba(255,255,255,0.08)",
                  background: active ? `${color}22` : "transparent",
                  color: active ? "#fff" : "#8b93a7",
                }}
              >
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
                {option}
              </Link>
            );
          })}
        </div>
        <div className="flex gap-2">
          {seasons.map((option) => (
            <Link
              key={option}
              href={`/equipos?liga=${encodeURIComponent(league)}&temporada=${option}`}
              className={`rounded-full px-3 py-1 text-xs font-semibold ${option === season ? "bg-white text-black" : "text-muted hover:text-ink"}`}
            >
              {seasonDisplay(option)}
            </Link>
          ))}
        </div>
      </div>

      {rows.length === 0 ? (
        <p className="glass rounded-3xl p-8 text-center text-muted">Todavía no hay datos de esta liga.</p>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Reveal>
              <div className="glass h-full rounded-3xl p-5">
                <h2 className="font-display text-lg font-bold">Los que más aprietan</h2>
                <p className="mb-3 text-xs text-muted">
                  PPDA: pases que dejan dar al rival antes de intentar robar. Cuanto más bajo, más presión.
                </p>
                <ol className="flex flex-col gap-1.5 text-sm">
                  {pressing.slice(0, 5).map((row, index) => (
                    <li key={row.team} className="flex justify-between">
                      <span>
                        <span className="mr-2 text-muted">{index + 1}.</span>
                        {row.team}
                      </span>
                      <span className="font-display font-bold tabular-nums">{row.ppda?.toFixed(1)}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </Reveal>
            <Reveal delay={0.05}>
              <div className="glass h-full rounded-3xl p-5">
                <h2 className="font-display text-lg font-bold">Suerte y mala suerte</h2>
                <p className="mb-3 text-xs text-muted">
                  Puntos reales menos puntos esperados. Muy positivo = está sacando más de lo que genera.
                </p>
                <ol className="flex flex-col gap-1.5 text-sm">
                  {[...luckiest.slice(0, 3), ...luckiest.slice(-2)].map((row) => {
                    const luck = row.points - row.xpts;
                    return (
                      <li key={row.team} className="flex justify-between">
                        <span>{row.team}</span>
                        <span className={`font-display font-bold tabular-nums ${luck >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
                          {signed(luck)}
                        </span>
                      </li>
                    );
                  })}
                </ol>
              </div>
            </Reveal>
          </div>

          <div className="glass overflow-x-auto rounded-3xl">
            <table className="w-full min-w-[860px] text-sm">
              <thead>
                <tr className="border-b border-line text-left text-[11px] uppercase tracking-[0.12em] text-muted">
                  <th className="px-4 py-3">#</th>
                  <th className="px-2 py-3">Equipo</th>
                  <th className="px-2 py-3 text-center">PJ</th>
                  <th className="px-2 py-3 text-center">V-E-D</th>
                  <th className="px-2 py-3 text-center">Goles</th>
                  <th className="px-2 py-3 text-center" title="Goles esperados a favor y en contra">xG</th>
                  <th className="px-2 py-3 text-center">Pts</th>
                  <th className="px-2 py-3 text-center" title="Puntos esperados según las ocasiones">xPts</th>
                  <th className="px-2 py-3 text-center" title="Pases permitidos por acción defensiva: menos = más presión">PPDA</th>
                  <th className="px-4 py-3">Forma</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const luck = row.points - row.xpts;
                  return (
                    <tr key={row.team} className="border-b border-line/60 hover:bg-white/[0.03]">
                      <td className="px-4 py-2.5 font-display font-bold text-muted">{row.position}</td>
                      <td className="px-2 py-2.5 font-semibold">
                        <Link
                          href={`/equipos/${encodeURIComponent(row.team)}?liga=${encodeURIComponent(league)}&temporada=${season}`}
                          className="hover:underline"
                        >
                          {row.team}
                        </Link>
                      </td>
                      <td className="px-2 py-2.5 text-center tabular-nums">{row.played}</td>
                      <td className="px-2 py-2.5 text-center tabular-nums text-muted">
                        {row.wins}-{row.draws}-{row.losses}
                      </td>
                      <td className="px-2 py-2.5 text-center tabular-nums">
                        {row.goals_for}:{row.goals_against}
                      </td>
                      <td className="px-2 py-2.5 text-center tabular-nums text-muted">
                        {row.xg_for.toFixed(1)}:{row.xg_against.toFixed(1)}
                      </td>
                      <td className="px-2 py-2.5 text-center font-display text-base font-bold tabular-nums">{row.points}</td>
                      <td className="px-2 py-2.5 text-center tabular-nums">
                        {row.xpts.toFixed(1)}{" "}
                        <span className={`text-xs ${luck >= 0 ? "text-emerald-300" : "text-rose-300"}`}>({signed(luck)})</span>
                      </td>
                      <td className="px-2 py-2.5 text-center tabular-nums">{row.ppda?.toFixed(1) ?? "—"}</td>
                      <td className="px-4 py-2.5">
                        <FormPills form={row.form} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
