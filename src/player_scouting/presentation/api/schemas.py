from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from player_scouting.application.ingestion_result import IngestionResult
from player_scouting.application.league_ingestion_job import LeagueIngestionJob
from player_scouting.application.ports import LeagueSummary
from player_scouting.application.use_cases.find_similar_players import (
    SimilarPlayerMatch,
)
from player_scouting.application.use_cases.process_league_ingestion_batch import (
    LeagueIngestionBatchSummary,
)
from player_scouting.domain.comparison import Comparison
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics


class PlayerSummaryOut(BaseModel):
    player_id: int
    name: str
    position: str
    date_of_birth: date
    photo_url: str | None = None
    preferred_foot: str | None = None
    latest_season_year: int | None = None


class PlayerOut(PlayerSummaryOut):
    goals: int
    assists: int
    shots: int
    shots_on_target: int
    expected_goals: float
    passes_completed: int
    passes_attempted: int
    key_passes: int
    dribbles_completed: int
    dribbles_attempted: int
    tackles_won: int
    interceptions: int
    fouls_committed: int
    fouls_won: int
    yellow_cards: int
    red_cards: int


class SeasonOut(BaseModel):
    competition: str
    label: str


class ComparisonOut(BaseModel):
    player1: PlayerSummaryOut
    player2: PlayerSummaryOut
    similarity_percentage: int


class SimilarPlayerMatchOut(BaseModel):
    comparison: ComparisonOut
    candidate_season: SeasonOut


class SkippedPlayerOut(BaseModel):
    player_id: int
    name: str
    reason: str


class IngestionResultOut(BaseModel):
    ingested: int
    skipped: list[SkippedPlayerOut]


class MarketValuePointOut(BaseModel):
    as_of: date
    amount_eur: int
    club: str


class MarketValueHistoryOut(BaseModel):
    current: MarketValuePointOut | None
    history: list[MarketValuePointOut]


class LeagueSummaryOut(BaseModel):
    id: int
    name: str
    country: str


class LeagueIngestionJobOut(BaseModel):
    id: int
    league_id: int
    league_name: str
    season_year: int
    next_page: int
    total_pages: int | None
    is_completed: bool


class LeagueIngestionBatchSummaryOut(BaseModel):
    pages_processed: int
    players_ingested: int


def player_summary_from_domain(
    player: Player, latest_season_year: int | None = None
) -> PlayerSummaryOut:
    return PlayerSummaryOut(
        player_id=player.player_id,
        name=player.name,
        position=player.position,
        date_of_birth=player.date_of_birth,
        photo_url=player.photo_url,
        preferred_foot=player.preferred_foot,
        latest_season_year=latest_season_year,
    )


def player_out_from_domain(
    player: Player, statistics: Statistics, latest_season_year: int | None = None
) -> PlayerOut:
    return PlayerOut(
        **player_summary_from_domain(player, latest_season_year).model_dump(),
        goals=statistics.goals,
        assists=statistics.assists,
        shots=statistics.shots,
        shots_on_target=statistics.shots_on_target,
        expected_goals=statistics.expected_goals,
        passes_completed=statistics.passes_completed,
        passes_attempted=statistics.passes_attempted,
        key_passes=statistics.key_passes,
        dribbles_completed=statistics.dribbles_completed,
        dribbles_attempted=statistics.dribbles_attempted,
        tackles_won=statistics.tackles_won,
        interceptions=statistics.interceptions,
        fouls_committed=statistics.fouls_committed,
        fouls_won=statistics.fouls_won,
        yellow_cards=statistics.yellow_cards,
        red_cards=statistics.red_cards,
    )


def season_out_from_domain(season: Season) -> SeasonOut:
    return SeasonOut(competition=season.competition, label=season.label)


def comparison_out_from_domain(comparison: Comparison) -> ComparisonOut:
    return ComparisonOut(
        player1=player_summary_from_domain(comparison.player1),
        player2=player_summary_from_domain(comparison.player2),
        similarity_percentage=comparison.similarity_score.percentage,
    )


def similar_player_match_out_from_domain(
    match: SimilarPlayerMatch,
) -> SimilarPlayerMatchOut:
    return SimilarPlayerMatchOut(
        comparison=comparison_out_from_domain(match.comparison),
        candidate_season=season_out_from_domain(match.candidate_season),
    )


def ingestion_result_out_from_domain(result: IngestionResult) -> IngestionResultOut:
    return IngestionResultOut(
        ingested=result.ingested,
        skipped=[
            SkippedPlayerOut(player_id=s.player_id, name=s.name, reason=s.reason)
            for s in result.skipped
        ],
    )


def market_value_point_out_from_domain(
    point: MarketValuePoint,
) -> MarketValuePointOut:
    return MarketValuePointOut(
        as_of=point.as_of, amount_eur=point.amount_eur, club=point.club
    )


def market_value_history_out_from_domain(
    points: list[MarketValuePoint],
) -> MarketValueHistoryOut:
    return MarketValueHistoryOut(
        current=market_value_point_out_from_domain(points[-1]) if points else None,
        history=[market_value_point_out_from_domain(point) for point in points],
    )


def league_summary_out_from_domain(summary: LeagueSummary) -> LeagueSummaryOut:
    return LeagueSummaryOut(id=summary.id, name=summary.name, country=summary.country)


def league_ingestion_job_out_from_domain(
    job: LeagueIngestionJob,
) -> LeagueIngestionJobOut:
    assert job.id is not None
    return LeagueIngestionJobOut(
        id=job.id,
        league_id=job.league_id,
        league_name=job.league_name,
        season_year=job.season_year,
        next_page=job.next_page,
        total_pages=job.total_pages,
        is_completed=job.is_completed,
    )


def league_ingestion_batch_summary_out_from_domain(
    summary: LeagueIngestionBatchSummary,
) -> LeagueIngestionBatchSummaryOut:
    return LeagueIngestionBatchSummaryOut(
        pages_processed=summary.pages_processed,
        players_ingested=summary.players_ingested,
    )
