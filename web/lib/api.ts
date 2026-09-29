const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type PlayerSummary = {
  player_id: number;
  name: string;
  position: string;
  date_of_birth: string;
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

export type Comparison = {
  player1: PlayerSummary;
  player2: PlayerSummary;
  similarity_percentage: number;
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

export function comparePlayers(
  playerIdA: number,
  playerIdB: number,
): Promise<Comparison> {
  return request<Comparison>(`/players/${playerIdA}/compare/${playerIdB}`);
}

export function findSimilarPlayers(
  playerId: number,
  top = 5,
): Promise<Comparison[]> {
  return request<Comparison[]>(`/players/${playerId}/similar?top=${top}`);
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
