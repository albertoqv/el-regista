const FOOT_LABELS: Record<string, string> = {
  left: "Zurdo",
  right: "Diestro",
  both: "Ambidiestro",
};

const POSITION_LABELS: Record<string, string> = {
  Forward: "Delantero",
  Midfielder: "Centrocampista",
  Defender: "Defensa",
  Goalkeeper: "Portero",
};

const POSITION_SHORT: Record<string, string> = {
  Forward: "DEL",
  Midfielder: "MED",
  Defender: "DEF",
  Goalkeeper: "POR",
};

export const COMPETITIONS = [
  "Premier League",
  "La Liga",
  "Bundesliga",
  "Serie A",
  "Ligue 1",
] as const;

/**
 * Leagues with player stats from the Transfermarkt dataset: goals, assists,
 * minutes and cards (no xG), and only for seasons the dataset already covers.
 */
export const OTHER_COMPETITIONS = [
  "Eredivisie",
  "Liga Portugal",
  "Süper Lig",
  "Jupiler Pro League",
  "Scottish Premiership",
  "Greek Super League",
  "Danish Superliga",
  "Ukrainian Premier League",
  "Russian Premier League",
] as const;

const COMPETITION_COLORS: Record<string, string> = {
  "Premier League": "#a855f7",
  "La Liga": "#ff4b44",
  Bundesliga: "#e11d48",
  "Serie A": "#22c55e",
  "Ligue 1": "#38bdf8",
  Eredivisie: "#f97316",
  "Liga Portugal": "#16a34a",
  "Süper Lig": "#dc2626",
  "Jupiler Pro League": "#facc15",
  "Scottish Premiership": "#2563eb",
  "Greek Super League": "#0ea5e9",
  "Danish Superliga": "#ef4444",
  "Ukrainian Premier League": "#eab308",
  "Russian Premier League": "#6366f1",
};

export function footLabel(foot: string): string {
  return FOOT_LABELS[foot] ?? foot;
}

export function positionLabel(position: string): string {
  return POSITION_LABELS[position] ?? position;
}

const DETAILED_POSITIONS: Record<string, string> = {
  "Centre-Forward": "Delantero centro",
  "Second Striker": "Segundo delantero",
  "Left Winger": "Extremo izquierdo",
  "Right Winger": "Extremo derecho",
  "Attacking Midfield": "Mediapunta",
  "Central Midfield": "Mediocentro",
  "Defensive Midfield": "Pivote",
  "Left Midfield": "Interior izquierdo",
  "Right Midfield": "Interior derecho",
  "Centre-Back": "Central",
  "Left-Back": "Lateral izquierdo",
  "Right-Back": "Lateral derecho",
  Goalkeeper: "Portero",
};

/** Transfermarkt's role in Spanish, falling back to the broad position. */
export function roleLabel(player: { position: string; detailed_position?: string | null }): string {
  if (player.detailed_position) {
    return DETAILED_POSITIONS[player.detailed_position] ?? player.detailed_position;
  }
  return positionLabel(player.position);
}

export function positionShort(position: string): string {
  return POSITION_SHORT[position] ?? position.slice(0, 3).toUpperCase();
}

export function competitionColor(competition: string): string {
  return COMPETITION_COLORS[competition] ?? "#3d8bff";
}

export function formatMarketValue(amountEur: number): string {
  if (amountEur >= 1_000_000) {
    return `${(amountEur / 1_000_000).toFixed(amountEur % 1_000_000 === 0 ? 0 : 1)}M €`;
  }
  if (amountEur >= 1_000) {
    return `${(amountEur / 1_000).toFixed(0)}k €`;
  }
  return `${amountEur} €`;
}

/** Transfermarkt serves a sharper 300x390 portrait under /portrait/big/. */
export function bigPhoto(photoUrl: string | null | undefined): string | null {
  if (!photoUrl) return null;
  return photoUrl.replace("/portrait/header/", "/portrait/big/");
}

/** Season that is being played now: it starts in July. */
export function currentSeasonStartYear(today: Date = new Date()): number {
  return today.getMonth() >= 6 ? today.getFullYear() : today.getFullYear() - 1;
}

/** "2026" -> "26/27"; other labels (e.g. "1983/1984") stay as they are. */
export function seasonDisplay(label: string): string {
  if (/^\d{4}$/.test(label)) {
    const start = Number(label);
    return `${String(start).slice(2)}/${String(start + 1).slice(2)}`;
  }
  return label;
}

export function formatAge(player: {
  date_of_birth: string | null;
  birth_year: number | null;
}): string | null {
  if (player.date_of_birth) {
    return String(calculateAge(player.date_of_birth));
  }
  if (player.birth_year) {
    return `~${new Date().getFullYear() - player.birth_year}`;
  }
  return null;
}

function calculateAge(dateOfBirth: string): number {
  const birth = new Date(dateOfBirth);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const hasNotHadBirthdayThisYear =
    today.getMonth() < birth.getMonth() ||
    (today.getMonth() === birth.getMonth() && today.getDate() < birth.getDate());
  if (hasNotHadBirthdayThisYear) {
    age -= 1;
  }
  return age;
}

/** Most recent season first (by start year, then competition). */
export function sortSeasonsByRecency<T extends { label: string; competition: string }>(
  seasons: T[],
): T[] {
  const year = (label: string) => Number(label.match(/\d{4}/)?.[0] ?? 0);
  return [...seasons].sort(
    (a, b) => year(b.label) - year(a.label) || a.competition.localeCompare(b.competition),
  );
}
