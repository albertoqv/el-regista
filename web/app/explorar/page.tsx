import type { Metadata } from "next";
import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { Reveal } from "@/app/components/motion";
import { ScoutNote } from "@/app/components/ScoutNote";
import { explorePlayers, type ExploreRow } from "@/lib/api";
import {
  COMPETITIONS,
  OTHER_COMPETITIONS,
  competitionColor,
  currentSeasonStartYear,
  formatMarketValue,
  positionLabel,
  seasonDisplay,
} from "@/lib/format";

export const metadata: Metadata = {
  title: "Explorador · El Regista",
  description:
    "Filtra jugadores por posición, edad, liga y precio, y ordénalos por cualquier métrica.",
};

const SORTS: { value: string; label: string; decimals: number }[] = [
  { value: "goals", label: "Goles", decimals: 0 },
  { value: "assists", label: "Asistencias", decimals: 0 },
  { value: "expected_goals", label: "xG", decimals: 2 },
  { value: "expected_assists", label: "xA", decimals: 2 },
  { value: "key_passes", label: "Pases clave", decimals: 0 },
  { value: "xg_chain", label: "xGChain", decimals: 2 },
  { value: "xg_buildup", label: "xGBuildup", decimals: 2 },
  { value: "shots", label: "Tiros", decimals: 0 },
  { value: "dribbles_completed", label: "Regates", decimals: 0 },
  { value: "passes_completed", label: "Pases completados", decimals: 0 },
  { value: "tackles_won", label: "Entradas ganadas", decimals: 0 },
  { value: "interceptions", label: "Intercepciones", decimals: 0 },
  { value: "fouls_won", label: "Faltas recibidas", decimals: 0 },
  { value: "minutes_played", label: "Minutos", decimals: 0 },
  { value: "market_value", label: "Valor de mercado", decimals: 0 },
  { value: "age", label: "Edad", decimals: 0 },
];

const POSITIONS = ["Forward", "Midfielder", "Defender", "Goalkeeper"];

const RECIPES: { label: string; note: string; params: Record<string, string> }[] = [
  {
    label: "Joyas sub-21",
    note: "jóvenes que ya rinden",
    params: { max_age: "21", sort: "expected_goals", per_90: "true", min_minutes: "450" },
  },
  {
    label: "Delanteros baratos que marcan",
    note: "hasta 15M",
    params: {
      position: "Forward",
      max_value: "15000000",
      sort: "goals",
      per_90: "true",
      min_minutes: "450",
    },
  },
  {
    label: "Creadores",
    note: "xA por 90",
    params: { sort: "expected_assists", per_90: "true", min_minutes: "450" },
  },
  {
    label: "Cerebros",
    note: "participan en todo",
    params: { position: "Midfielder", sort: "xg_buildup", per_90: "true", min_minutes: "450" },
  },
  {
    label: "Muros",
    note: "defensas que roban",
    params: { position: "Defender", sort: "interceptions", per_90: "true", min_minutes: "450" },
  },
  {
    label: "Gangas absolutas",
    note: "hasta 5M con goles",
    params: { max_value: "5000000", sort: "goals", min_minutes: "300" },
  },
];

function param(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? "";
}

function show(row: ExploreRow, sort: string, perNinety: boolean): string {
  if (sort === "market_value") {
    return row.market_value_eur ? formatMarketValue(row.market_value_eur) : "—";
  }
  const decimals = perNinety && sort !== "age" ? 2 : (SORTS.find((s) => s.value === sort)?.decimals ?? 0);
  return row.sort_value.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-xs">
      <span className="font-semibold uppercase tracking-[0.15em] text-muted">{label}</span>
      {children}
    </label>
  );
}

const INPUT = "glass rounded-xl px-3 py-2 text-sm text-ink outline-none focus:border-white/30";

export default async function ExplorePage(props: PageProps<"/explorar">) {
  const searchParams = await props.searchParams;
  const current = String(currentSeasonStartYear());
  const values = {
    season: param(searchParams.season) || current,
    competition: param(searchParams.competition),
    position: param(searchParams.position),
    min_age: param(searchParams.min_age),
    max_age: param(searchParams.max_age),
    max_value: param(searchParams.max_value),
    min_minutes: param(searchParams.min_minutes) || "270",
    sort: param(searchParams.sort) || "goals",
    per_90: param(searchParams.per_90) === "true",
  };

  const query = new URLSearchParams({
    season: values.season,
    sort: values.sort,
    min_minutes: values.min_minutes,
    limit: "60",
  });
  for (const key of ["competition", "position", "min_age", "max_age", "max_value"] as const) {
    if (values[key]) query.set(key, values[key]);
  }
  if (values.per_90) query.set("per_90", "true");
  if (values.sort === "age") query.set("ascending", "true");

  const rows = await explorePlayers(query).catch((): ExploreRow[] => []);
  const sortLabel = SORTS.find((entry) => entry.value === values.sort)?.label ?? values.sort;
  const perNinetyShown = values.per_90 && values.sort !== "market_value" && values.sort !== "age";
  const seasons = [0, 1, 2].map((offset) => String(Number(current) - offset));
  const otherLeague = (OTHER_COMPETITIONS as readonly string[]).includes(values.competition);
  const stringValues: Record<string, string> = Object.fromEntries(
    Object.entries({ ...values, per_90: values.per_90 ? "true" : "" }).filter(([, value]) => value),
  );

  return (
    <div className="flex flex-col gap-8">
      <Reveal>
        <ScoutNote rotate={-2}>como un Wyscout, pero gratis</ScoutNote>
        <h1 className="font-display text-4xl font-bold tracking-tight sm:text-5xl">Explorador</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">Filtra y ordena por cualquier métrica.</p>
      </Reveal>

      <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0">
        {RECIPES.map((recipe, index) => (
          <Link
            key={recipe.label}
            href={`/explorar?${new URLSearchParams({ season: values.season, ...recipe.params }).toString()}`}
            className="glass glass-hover shrink-0 rounded-lg px-4 py-2.5"
            style={{ transform: `rotate(${index % 2 ? 1 : -1}deg)` }}
          >
            <span className="block text-sm font-semibold">{recipe.label}</span>
            <span className="font-hand text-base text-[#f2c230]">{recipe.note}</span>
          </Link>
        ))}
      </div>

      <form
        method="get"
        className="glass grid grid-cols-2 gap-3 rounded-lg p-4 sm:grid-cols-3 lg:grid-cols-5"
      >
        <Field label="Temporada">
          <select name="season" defaultValue={values.season} className={INPUT}>
            {seasons.map((season) => (
              <option key={season} value={season}>
                {seasonDisplay(season)}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Liga">
          <select name="competition" defaultValue={values.competition} className={INPUT}>
            <option value="">Todas</option>
            <optgroup label="5 grandes (con xG)">
              {COMPETITIONS.map((league) => (
                <option key={league} value={league}>
                  {league}
                </option>
              ))}
            </optgroup>
            <optgroup label="Más ligas (goles, asistencias, minutos)">
              {OTHER_COMPETITIONS.map((league) => (
                <option key={league} value={league}>
                  {league}
                </option>
              ))}
            </optgroup>
          </select>
        </Field>
        <Field label="Posición">
          <select name="position" defaultValue={values.position} className={INPUT}>
            <option value="">Todas</option>
            {POSITIONS.map((position) => (
              <option key={position} value={position}>
                {positionLabel(position)}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Edad">
          <div className="flex gap-2">
            <input
              name="min_age"
              type="number"
              min={14}
              max={50}
              placeholder="mín"
              defaultValue={values.min_age}
              className={`${INPUT} w-full`}
            />
            <input
              name="max_age"
              type="number"
              min={14}
              max={50}
              placeholder="máx"
              defaultValue={values.max_age}
              className={`${INPUT} w-full`}
            />
          </div>
        </Field>
        <Field label="Valor máximo">
          <select name="max_value" defaultValue={values.max_value} className={INPUT}>
            <option value="">Sin límite</option>
            {[100, 50, 30, 15, 5, 2].map((millions) => (
              <option key={millions} value={String(millions * 1_000_000)}>
                Hasta {millions}M €
              </option>
            ))}
          </select>
        </Field>
        <Field label="Minutos mínimos">
          <input
            name="min_minutes"
            type="number"
            min={0}
            step={90}
            defaultValue={values.min_minutes}
            className={INPUT}
          />
        </Field>
        <Field label="Ordenar por">
          <select name="sort" defaultValue={values.sort} className={INPUT}>
            {SORTS.map((entry) => (
              <option key={entry.value} value={entry.value}>
                {entry.label}
              </option>
            ))}
          </select>
        </Field>
        <label className="flex items-end gap-2 pb-2 text-sm">
          <input
            name="per_90"
            type="checkbox"
            value="true"
            defaultChecked={values.per_90}
            className="h-4 w-4 accent-[#f2c230]"
          />
          Por 90 minutos
        </label>
        <div className="col-span-2 flex items-end gap-2 sm:col-span-1 lg:col-span-2">
          <button
            type="submit"
            className="flex-1 rounded-full bg-[#f2c230] px-5 py-2.5 text-sm font-bold text-bg transition hover:brightness-105"
          >
            Buscar
          </button>
          <Link
            href="/explorar"
            className="rounded-full border border-line px-4 py-2.5 text-sm text-muted hover:text-ink"
          >
            Limpiar
          </Link>
        </div>
      </form>

      {otherLeague ? (
        <p className="-mt-4 px-2 text-xs text-muted">
          En {values.competition} tenemos goles, asistencias, minutos y tarjetas (dataset de
          Transfermarkt); xG, pases y regates solo existen para las 5 grandes.
        </p>
      ) : null}

      {rows.length === 0 ? (
        <p className="glass rounded-lg p-8 text-center text-muted">
          {otherLeague && values.season === current ? (
            <>
              <ScoutNote rotate={-2}>todavía sin datos</ScoutNote>
              <br />
              {values.competition} aún no tiene datos de {seasonDisplay(current)}: esa fuente se
              actualiza con retraso.{" "}
              <Link
                href={`/explorar?${new URLSearchParams({ ...stringValues, season: String(Number(current) - 1) }).toString()}`}
                className="text-brand-2 hover:underline"
              >
                Ver {seasonDisplay(String(Number(current) - 1))}
              </Link>
            </>
          ) : (
            <>
              <ScoutNote rotate={-2}>nadie cumple todo eso…</ScoutNote>
              <br />
              Prueba a relajar algún filtro.
            </>
          )}
        </p>
      ) : (
        <div className="glass overflow-x-auto rounded-lg">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-line text-left text-[11px] uppercase tracking-[0.15em] text-muted">
                <th className="px-4 py-3">#</th>
                <th className="px-2 py-3">Jugador</th>
                <th className="px-2 py-3">Edad</th>
                <th className="px-2 py-3">Valor</th>
                <th className="px-2 py-3">Min</th>
                <th className="px-2 py-3">G</th>
                <th className="px-2 py-3">A</th>
                <th className="px-2 py-3">xG</th>
                <th className="px-2 py-3">xA</th>
                <th className="px-4 py-3 text-right text-[#f2c230]">
                  {sortLabel}
                  {perNinetyShown ? " /90" : ""}
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr
                  key={`${row.player_id}-${row.competition}`}
                  className="border-b border-line/60 transition hover:bg-white/[0.03]"
                >
                  <td className="px-4 py-2.5 font-display font-bold text-muted">{index + 1}</td>
                  <td className="px-2 py-2.5">
                    <Link
                      href={`/players/${row.player_id}?sc=${encodeURIComponent(row.competition)}&sl=${encodeURIComponent(row.season_label)}`}
                      className="flex items-center gap-3"
                    >
                      <Avatar name={row.name} photoUrl={row.photo_url} size={34} />
                      <span className="flex flex-col">
                        <span className="font-semibold">{row.name}</span>
                        <span className="flex items-center gap-1.5 text-xs text-muted">
                          <span
                            className="h-1.5 w-1.5 rounded-full"
                            style={{ background: competitionColor(row.competition) }}
                          />
                          {row.team ?? row.competition} · {positionLabel(row.position)}
                        </span>
                      </span>
                    </Link>
                  </td>
                  <td className="px-2 py-2.5 tabular-nums">{row.age ?? "—"}</td>
                  <td className="px-2 py-2.5 tabular-nums">
                    {row.market_value_eur ? formatMarketValue(row.market_value_eur) : "—"}
                  </td>
                  <td className="px-2 py-2.5 tabular-nums text-muted">{row.minutes_played}</td>
                  <td className="px-2 py-2.5 tabular-nums">{row.goals}</td>
                  <td className="px-2 py-2.5 tabular-nums">{row.assists}</td>
                  <td className="px-2 py-2.5 tabular-nums text-muted">
                    {row.expected_goals.toFixed(1)}
                  </td>
                  <td className="px-2 py-2.5 tabular-nums text-muted">
                    {row.expected_assists.toFixed(1)}
                  </td>
                  <td className="px-4 py-2.5 text-right font-display text-base font-bold tabular-nums text-[#f2c230]">
                    {show(row, values.sort, values.per_90)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
