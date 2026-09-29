const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type PlayerSummary = {
  player_id: number;
  name: string;
  position: string;
  date_of_birth: string;
  photo_url: string | null;
  preferred_foot: string | null;
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
};

export type Season = {
  competition: string;
  label: string;
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

export type SkippedPlayer = {
  player_id: number;
  name: string;
  reason: string;
};

export type IngestionResult = {
  ingested: number;
  skipped: SkippedPlayer[];
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

export type LeagueSummary = {
  id: number;
  name: string;
  country: string;
};

export type LeagueIngestionJob = {
  id: number;
  league_id: number;
  league_name: string;
  season_year: number;
  next_page: number;
  total_pages: number | null;
  is_completed: boolean;
};

export type LeagueIngestionBatchSummary = {
  pages_processed: number;
  players_ingested: number;
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
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, body || response.statusText);
  }
  return response.json() as Promise<T>;
}

export function listPlayers(): Promise<Player[]> {
  return request<Player[]>("/players");
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

export function ingestCompetition(
  competitionId: number,
  seasonId: number,
): Promise<IngestionResult> {
  return request<IngestionResult>(
    `/ingestion/statsbomb/${competitionId}/${seasonId}`,
    { method: "POST" },
  );
}

export function ingestApiFootballPlayer(
  name: string,
  leagueId: number,
  seasonYear: number,
): Promise<IngestionResult> {
  const params = new URLSearchParams({
    name,
    league: String(leagueId),
    season: String(seasonYear),
  });
  return request<IngestionResult>(`/ingestion/api-football/players?${params}`, {
    method: "POST",
  });
}

export function ingestTransfermarktPlayer(
  playerId: number,
  name: string,
): Promise<IngestionResult> {
  const params = new URLSearchParams({ player_id: String(playerId), name });
  return request<IngestionResult>(`/ingestion/transfermarkt/players?${params}`, {
    method: "POST",
  });
}

export function searchLeagues(query: string): Promise<LeagueSummary[]> {
  const params = new URLSearchParams({ q: query });
  return request<LeagueSummary[]>(`/ingestion/leagues/search?${params}`);
}

export function enqueueLeagueIngestion(
  leagueId: number,
  leagueName: string,
  seasonYear: number,
): Promise<LeagueIngestionJob> {
  const params = new URLSearchParams({
    league_id: String(leagueId),
    league_name: leagueName,
    season_year: String(seasonYear),
  });
  return request<LeagueIngestionJob>(`/ingestion/leagues?${params}`, {
    method: "POST",
  });
}

export function listLeagueIngestionJobs(): Promise<LeagueIngestionJob[]> {
  return request<LeagueIngestionJob[]>("/ingestion/leagues");
}

export function processLeagueIngestionBatch(
  budget?: number,
): Promise<LeagueIngestionBatchSummary> {
  const params = budget ? `?budget=${budget}` : "";
  return request<LeagueIngestionBatchSummary>(
    `/ingestion/leagues/process${params}`,
    { method: "POST" },
  );
}
