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
  height_cm?: number | null;
  detailed_position?: string | null;
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

export type ShotMetric =
  | "late_goals"
  | "decisive_goals"
  | "late_decisive_goals"
  | "headed_goals"
  | "outside_box_goals"
  | "set_piece_goals"
  | "finishing"
  | "npxg_per_shot";

export type ShotLeader = PlayerSummary & {
  competition: string;
  team: string | null;
  value: number;
  goals: number;
  shots: number;
};

export function listShotLeaders(
  startYear: number,
  options?: { metric?: ShotMetric; limit?: number; competition?: string },
): Promise<ShotLeader[]> {
  const params = new URLSearchParams();
  if (options?.metric) params.set("metric", options.metric);
  if (options?.limit) params.set("limit", String(options.limit));
  if (options?.competition) params.set("competition", options.competition);
  const query = params.toString();
  return request<ShotLeader[]>(`/seasons/${startYear}/shot-leaders${query ? `?${query}` : ""}`);
}

export type Partnership = {
  scorer: PlayerSummary;
  assister_name: string;
  assister: PlayerSummary | null;
  team: string;
  competition: string;
  goals: number;
};

export function listPartnerships(
  startYear: number,
  options?: { limit?: number; competition?: string },
): Promise<Partnership[]> {
  const params = new URLSearchParams();
  if (options?.limit) params.set("limit", String(options.limit));
  if (options?.competition) params.set("competition", options.competition);
  const query = params.toString();
  return request<Partnership[]>(`/seasons/${startYear}/partnerships${query ? `?${query}` : ""}`);
}

export type PlayerShot = {
  minute: number;
  result: string;
  x: number;
  y: number;
  xg: number;
  situation: string;
  shot_type: string;
  decisive: boolean;
  assisted_by: string | null;
  competition: string;
  season_label: string;
  team: string;
  opponent: string;
  played_on: string;
};

export function getPlayerShots(playerId: number, seasonLabel?: string): Promise<PlayerShot[]> {
  const query = seasonLabel ? `?season_label=${encodeURIComponent(seasonLabel)}` : "";
  return request<PlayerShot[]>(`/players/${playerId}/shots${query}`);
}

export type ExploreRow = SeasonLeader & {
  market_value_eur: number | null;
  age: number | null;
  sort_value: number;
};

export function explorePlayers(params: URLSearchParams): Promise<ExploreRow[]> {
  const query = params.toString();
  return request<ExploreRow[]>(`/players/explore${query ? `?${query}` : ""}`);
}

export type TableRow = {
  position: number;
  team: string;
  competition: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  points: number;
  xg_for: number;
  xg_against: number;
  npxg_difference: number;
  xpts: number;
  ppda: number | null;
  ppda_allowed: number | null;
  deep: number;
  deep_allowed: number;
  form: string[];
};

export function getLeagueTable(season: string, competition: string): Promise<TableRow[]> {
  const query = new URLSearchParams({ season, competition }).toString();
  return request<TableRow[]>(`/teams/table?${query}`);
}

export type TeamMatch = {
  match_id: number;
  competition: string;
  season_label: string;
  played_on: string;
  team: string;
  opponent: string;
  home: boolean;
  goals_for: number;
  goals_against: number;
  xg_for: number;
  xg_against: number;
  ppda: number | null;
  deep: number;
  deep_allowed: number;
  xpts: number;
  result: string;
};

export function getTeamMatches(team: string, season: string): Promise<TeamMatch[]> {
  const query = new URLSearchParams({ team, season }).toString();
  return request<TeamMatch[]>(`/teams/matches?${query}`);
}

export function getTeamPlayers(team: string, season: string): Promise<ShotLeader[]> {
  const query = new URLSearchParams({ team, season }).toString();
  return request<ShotLeader[]>(`/teams/players?${query}`);
}

export type Forecast = {
  match_id: number;
  competition: string;
  kickoff: string;
  home_team: string;
  away_team: string;
  home_win: number;
  draw: number;
  away_win: number;
  expected_home: number;
  expected_away: number;
  scorelines: { home: number; away: number; probability: number }[];
  over_2_5: number;
  both_teams_score: number;
  home_form: string[];
  away_form: string[];
};

export function getPredictions(days: number, competition?: string): Promise<Forecast[]> {
  const params = new URLSearchParams({ days: String(days) });
  if (competition) params.set("competition", competition);
  return request<Forecast[]>(`/predictions?${params.toString()}`);
}

export type Backtest = {
  matches: number;
  accuracy: number;
  brier: number;
  log_loss: number;
  baseline_accuracy: number;
  baseline_brier: number;
  calibration: { predicted: number; observed: number; count: number }[];
};

export function getBacktest(season: string, competition?: string): Promise<Backtest> {
  const params = new URLSearchParams({ season });
  if (competition) params.set("competition", competition);
  return request<Backtest>(`/predictions/backtest?${params.toString()}`);
}

export type Outcome = { home_win: number; draw: number; away_win: number };
export type LineProbability = { line: number; over: number };
export type StatForecast = {
  stat: string;
  expected_home: number;
  expected_away: number;
  expected_total: number;
  home_more: number;
  equal: number;
  away_more: number;
  over: LineProbability[];
  distribution: number[];
};
export type MatchLine = {
  played_on: string;
  home_team: string;
  away_team: string;
  home_goals: number | null;
  away_goals: number | null;
  home_corners: number | null;
  away_corners: number | null;
  home_yellows: number | null;
  away_yellows: number | null;
  home_shots: number | null;
  away_shots: number | null;
};
export type MatchInsights = {
  match_id: number;
  competition: string;
  kickoff: string;
  home_team: string;
  away_team: string;
  expected_home: number;
  expected_away: number;
  result: Outcome;
  market: Outcome | null;
  consensus: Outcome;
  scorelines: { home: number; away: number; probability: number }[];
  goals_over: LineProbability[];
  both_teams_score: number;
  home_clean_sheet: number;
  away_clean_sheet: number;
  half_time: Outcome;
  stats: StatForecast[];
  referee: { name: string; matches: number; yellows_per_match: number; multiplier: number } | null;
  head_to_head: MatchLine[];
  home_recent: MatchLine[];
  away_recent: MatchLine[];
};
export function getMatchInsights(matchId: number): Promise<MatchInsights> {
  return request<MatchInsights>(`/predictions/${matchId}/insights`);
}
export type PlayerMarket = {
  understat_player_id: number;
  player_id: number | null;
  name: string;
  photo_url: string | null;
  position: string;
  plays: number;
  expected_minutes: number;
  goal: number;
  assist: number;
  card: number;
  shots_1: number;
  shots_2: number;
};
export type PlayerMarkets = { match_id: number; home_team: string; away_team: string; home: PlayerMarket[]; away: PlayerMarket[] };
export function getPlayerMarkets(matchId: number): Promise<PlayerMarkets> {
  return request<PlayerMarkets>(`/predictions/${matchId}/players`);
}

export type Pick = {
  match_id: number;
  competition: string;
  kickoff: string;
  home_team: string;
  away_team: string;
  category: "result" | "goals" | "corners" | "cards" | "scorers";
  label: string;
  probability: number;
};
export type Highlights = { window_start: string; window_end: string; picks: Pick[] };
export function getHighlights(perCategory = 5): Promise<Highlights> {
  return request<Highlights>(`/predictions/highlights?per_category=${perCategory}`);
}

export type StatBacktest = {
  stat: string;
  matches: number;
  model_mae: number;
  baseline_mae: number;
  line: number;
  model_brier: number;
  baseline_brier: number;
};

export function getStatsBacktest(competition: string, season: string): Promise<StatBacktest[]> {
  const query = new URLSearchParams({ competition, season }).toString();
  return request<StatBacktest[]>(`/predictions/stats-backtest?${query}`);
}

export type PlayersBacktest = {
  predictions: number;
  brier: number;
  baseline_brier: number;
  calibration: { predicted: number; observed: number; count: number }[];
};

export function getPlayersBacktest(competition: string, season: string): Promise<PlayersBacktest> {
  const query = new URLSearchParams({ competition, season }).toString();
  return request<PlayersBacktest>(`/predictions/players-backtest?${query}`);
}

export type Overview = {
  players: number;
  players_with_photo: number;
  player_seasons: number;
  competitions: number;
  matches_with_shots: number;
  shots: number;
  match_stats: number;
  fixtures: number;
};

export function getOverview(): Promise<Overview> {
  return request<Overview>("/overview");
}

export type MarketBenchmark = {
  matches: number;
  model_brier: number;
  market_brier: number;
  consensus_brier: number;
  model_accuracy: number;
  market_accuracy: number;
};

export function getMarketBenchmark(season: string): Promise<MarketBenchmark> {
  return request<MarketBenchmark>(`/predictions/market-benchmark?season=${season}`);
}
