const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REVALIDATE_SECONDS = 600;

export type PlayerSummary = {
  player_id: number;
  name: string;
  position: string;
  date_of_birth: string | null;
  birth_year: number | null;
  photo_url: string | null;
  preferred_foot: string | null;
  latest_season_year: number | null;
};

export type Player = PlayerSummary & {
  goals: number;
  assists: number;
  shots: number;
  shots_on_target: number;
  expected_goals: number;
  passes_completed: number;
  passes_attempted: number;
  key_passes: number;
  dribbles_completed: number;
  dribbles_attempted: number;
  tackles_won: number;
  interceptions: number;
  fouls_committed: number;
  fouls_won: number;
  yellow_cards: number;
  red_cards: number;
  minutes_played: number;
  expected_assists: number;
  xg_chain: number;
  xg_buildup: number;
};

export type Season = {
  competition: string;
  label: string;
  team?: string | null;
};

export type Comparison = {
  player1: PlayerSummary;
  player2: PlayerSummary;
  similarity_percentage: number;
};

export type SimilarPlayerMatch = {
  comparison: Comparison;
  candidate_season: Season;
};

export type MarketValuePoint = {
  as_of: string;
  amount_eur: number;
  club: string;
};

export type MarketValueHistory = {
  current: MarketValuePoint | null;
  history: MarketValuePoint[];
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // Data changes weekly: let the server cache responses for a few minutes.
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    next: { revalidate: REVALIDATE_SECONDS },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, body || response.statusText);
  }
  return response.json() as Promise<T>;
}

export type PlayerSort = "recent" | "goals" | "assists";

export function listPlayers(options?: {
  q?: string;
  sort?: PlayerSort;
  limit?: number;
}): Promise<Player[]> {
  const params = new URLSearchParams();
  if (options?.q) params.set("q", options.q);
  if (options?.sort) params.set("sort", options.sort);
  if (options?.limit) params.set("limit", String(options.limit));
  const query = params.toString();
  return request<Player[]>(`/players${query ? `?${query}` : ""}`);
}

export function getPlayer(playerId: number): Promise<Player> {
  return request<Player>(`/players/${playerId}`);
}

export function listPlayerSeasons(playerId: number): Promise<Season[]> {
  return request<Season[]>(`/players/${playerId}/seasons`);
}

export function getPlayerSeason(
  playerId: number,
  season: Season,
): Promise<Player> {
  return request<Player>(
    `/players/${playerId}/seasons/${encodeURIComponent(season.competition)}/${encodeURIComponent(season.label)}`,
  );
}

export function comparePlayers(
  playerIdA: number,
  playerIdB: number,
  options?: { seasonA?: Season; seasonB?: Season },
): Promise<Comparison> {
  const params = new URLSearchParams();
  if (options?.seasonA) {
    params.set("season_a_competition", options.seasonA.competition);
    params.set("season_a_label", options.seasonA.label);
  }
  if (options?.seasonB) {
    params.set("season_b_competition", options.seasonB.competition);
    params.set("season_b_label", options.seasonB.label);
  }
  const query = params.toString();
  return request<Comparison>(
    `/players/${playerIdA}/compare/${playerIdB}${query ? `?${query}` : ""}`,
  );
}

export function getMarketValue(playerId: number): Promise<MarketValueHistory> {
  return request<MarketValueHistory>(`/players/${playerId}/market-value`);
}

export function findSimilarPlayers(
  playerId: number,
  options?: { top?: number; season?: Season },
): Promise<SimilarPlayerMatch[]> {
  const params = new URLSearchParams();
  if (options?.top) params.set("top", String(options.top));
  if (options?.season) {
    params.set("season_competition", options.season.competition);
    params.set("season_label", options.season.label);
  }
  const query = params.toString();
  return request<SimilarPlayerMatch[]>(
    `/players/${playerId}/similar${query ? `?${query}` : ""}`,
  );
}

export type SeasonLeader = Player & {
  competition: string;
  season_label: string;
  team: string | null;
};

export type LeaderMetric =
  | "goals"
  | "assists"
  | "expected_goals"
  | "expected_assists"
  | "shots"
  | "key_passes"
  | "xg_chain"
  | "dribbles_completed"
  | "tackles_won"
  | "interceptions";

export function listSeasonLeaders(
  startYear: number,
  options?: { metric?: LeaderMetric; limit?: number; competition?: string },
): Promise<SeasonLeader[]> {
  const params = new URLSearchParams();
  if (options?.metric) params.set("metric", options.metric);
  if (options?.limit) params.set("limit", String(options.limit));
  if (options?.competition) params.set("competition", options.competition);
  const query = params.toString();
  return request<SeasonLeader[]>(
    `/seasons/${startYear}/leaders${query ? `?${query}` : ""}`,
  );
}

export type MetricPercentile = { per_90: number; percentile: number };

export type PercentileReport = {
  competition: string;
  season_label: string;
  position: string;
  peer_count: number;
  minimum_minutes: number;
  metrics: Record<string, MetricPercentile>;
};

export function getPlayerPercentiles(
  playerId: number,
  season: Season,
): Promise<PercentileReport> {
  return request<PercentileReport>(
    `/players/${playerId}/seasons/${encodeURIComponent(season.competition)}/${encodeURIComponent(season.label)}/percentiles`,
  );
}

export type TwinProfile = PlayerSummary & {
  competition: string;
  season_label: string;
  team: string | null;
  market_value_eur: number | null;
  percentiles: Record<string, number>;
};

export type Twin = TwinProfile & {
  similarity: number;
  shared_strengths: string[];
  differences: string[];
};

export type TwinReport = { target: TwinProfile; twins: Twin[] };

export type TwinQuery = {
  season?: Season;
  maxValue?: number;
  maxAge?: number;
  league?: string;
  limit?: number;
};

export function findTwins(playerId: number, query: TwinQuery = {}): Promise<TwinReport> {
  const params = new URLSearchParams();
  if (query.season) {
    params.set("competition", query.season.competition);
    params.set("label", query.season.label);
  }
  if (query.maxValue) params.set("max_value", String(query.maxValue));
  if (query.maxAge) params.set("max_age", String(query.maxAge));
  if (query.league) params.set("league", query.league);
  if (query.limit) params.set("limit", String(query.limit));
  const search = params.toString();
  return request<TwinReport>(`/players/${playerId}/twins${search ? `?${search}` : ""}`);
}
