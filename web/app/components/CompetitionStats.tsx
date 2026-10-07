import type { CompetitionLine } from "@/lib/api";
import { seasonDisplay } from "@/lib/format";

// Seasons shown open; older ones fold away.
const OPEN_SEASONS = 3;

// Finals tournaments carry their year (Mundial 2026); the rest a season (Nations League 26/27).
const TOURNAMENTS = new Set(["Mundial", "Eurocopa", "Copa América", "Copa África", "Copa Asia", "Copa Confederaciones"]);

function nationalLabel(line: CompetitionLine) {
  return TOURNAMENTS.has(line.competition) ? line.season_label : seasonDisplay(line.season_label);
}

function sum(lines: CompetitionLine[], key: "appearances" | "goals" | "assists" | "minutes_played") {
  return lines.reduce((total, line) => total + line[key], 0);
}

function LinesTable({
  lines,
  total,
  showTeam = true,
}: {
  lines: CompetitionLine[];
  total?: string;
  showTeam?: boolean;
}) {
  return (
    <div>
      {/* Fixed columns: every season's table lines up with the others. */}
      <table className="w-full table-fixed text-sm">
        <colgroup>
          <col />
          <col className="w-16 sm:w-20" />
          <col className="w-14 sm:w-16" />
          <col className="w-14 sm:w-16" />
          <col className="w-0 sm:w-20" />
        </colgroup>
        <thead>
          <tr className="text-left text-xs text-muted">
            <th className="py-1 font-normal">Competición</th>
            <th className="text-right font-normal">Partidos</th>
            <th className="text-right font-normal">Goles</th>
            <th className="text-right font-normal">Asist.</th>
            <th className="hidden text-right font-normal sm:table-cell">Minutos</th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line) => (
            <tr key={`${line.competition}-${line.season_label}`} className="border-t border-line/60">
              <td className="py-1.5">
                {line.competition}
                {showTeam && line.team && <span className="text-muted"> · {line.team}</span>}
              </td>
              <td className="text-right tabular-nums">{line.appearances}</td>
              <td className="text-right tabular-nums">{line.goals}</td>
              <td className="text-right tabular-nums">{line.assists}</td>
              <td className="hidden text-right tabular-nums text-muted sm:table-cell">
                {line.minutes_played.toLocaleString("es-ES")}
              </td>
            </tr>
          ))}
          {total && lines.length > 1 && (
            <tr className="border-t border-ink font-semibold">
              <td className="py-1.5">{total}</td>
              <td className="text-right tabular-nums">{sum(lines, "appearances")}</td>
              <td className="text-right tabular-nums">{sum(lines, "goals")}</td>
              <td className="text-right tabular-nums">{sum(lines, "assists")}</td>
              <td className="hidden text-right tabular-nums text-muted sm:table-cell">
                {sum(lines, "minutes_played").toLocaleString("es-ES")}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function ClubSeason({ label, lines }: { label: string; lines: CompetitionLine[] }) {
  // One club all season: named once in the heading, not on every line.
  const teams = new Set(lines.map((line) => line.team));
  const team = teams.size === 1 ? lines[0].team : null;
  return (
    <div className="flex flex-col gap-1">
      <h3 className="font-heading text-lg tracking-tight">
        Temporada {seasonDisplay(label)}
        {team && <span className="font-normal text-muted"> · {team}</span>}
      </h3>
      <LinesTable lines={lines} total="Total" showTeam={!team} />
    </div>
  );
}

/** League, Europe, cups and super cups season by season, and the national team apart. */
export function CompetitionStats({ lines }: { lines: CompetitionLine[] }) {
  const club = lines.filter((line) => line.kind !== "national");
  const national = lines.filter((line) => line.kind === "national");
  const seasons = [...new Set(club.map((line) => line.season_label))];
  const bySeason = (label: string) => club.filter((line) => line.season_label === label);
  if (lines.length === 0) return null;

  return (
    <section className="flex flex-col gap-6">
      <div>
        <h2 className="font-heading text-2xl tracking-tight">Por competición</h2>
        <p className="text-sm text-muted">Liga, Europa y copas, temporada a temporada.</p>
      </div>
      {seasons.slice(0, OPEN_SEASONS).map((label) => (
        <ClubSeason key={label} label={label} lines={bySeason(label)} />
      ))}
      {seasons.length > OPEN_SEASONS && (
        <details className="group flex flex-col gap-4">
          <summary className="cursor-pointer text-sm font-semibold text-muted hover:text-ink">
            Temporadas anteriores
          </summary>
          <div className="mt-4 flex flex-col gap-6">
            {seasons.slice(OPEN_SEASONS).map((label) => (
              <ClubSeason key={label} label={label} lines={bySeason(label)} />
            ))}
          </div>
        </details>
      )}
      {national.length > 0 && (
        <div className="flex flex-col gap-1">
          <h3 className="font-heading text-lg tracking-tight">Con su selección</h3>
          <LinesTable
            lines={national.map((line) => ({ ...line, competition: `${line.competition} ${nationalLabel(line)}` }))}
          />
        </div>
      )}
    </section>
  );
}
