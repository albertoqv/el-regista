from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from player_scouting.application.ingestion_result import IngestionResult
from player_scouting.application.league_ingestion_job import LeagueIngestionJob
from player_scouting.application.ports import (
    LeagueSummary,
    Partnership,
    PlayerShot,
    SeasonRecord,
    ShotLeader,
)
from player_scouting.application.use_cases.find_similar_players import (
    SimilarPlayerMatch,
)
from player_scouting.application.use_cases.find_twins import TwinProfile, TwinReport
from player_scouting.application.use_cases.get_player_percentiles import (
    PercentileReport,
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
    date_of_birth: date | None
    birth_year: int | None = None
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
    minutes_played: int
    expected_assists: float
    xg_chain: float
    xg_buildup: float


class SeasonOut(BaseModel):
    competition: str
    label: str
    team: str | None = None


class SeasonLeaderOut(PlayerOut):
    competition: str
    season_label: str
    team: str | None


class MetricPercentileOut(BaseModel):
    per_90: float
    percentile: int


class PercentileReportOut(BaseModel):
    competition: str
    season_label: str
    position: str
    peer_count: int
    minimum_minutes: int
    metrics: dict[str, MetricPercentileOut]


class TwinProfileOut(PlayerSummaryOut):
    competition: str
    season_label: str
    team: str | None
    market_value_eur: int | None
    percentiles: dict[str, int]


class TwinOut(TwinProfileOut):
    similarity: int
    shared_strengths: list[str]
    differences: list[str]


class TwinReportOut(BaseModel):
    target: TwinProfileOut
    twins: list[TwinOut]


class PendingEnrichmentOut(BaseModel):
    player_id: int
    name: str
    birth_year: int | None


class MarketValuePointIn(BaseModel):
    as_of: date
    amount_eur: int
    club: str


class EnrichmentIn(BaseModel):
    found: bool
    photo_url: str | None = None
    date_of_birth: date | None = None
    preferred_foot: str | None = None
    market_values: list[MarketValuePointIn] = []


class ShotLeaderOut(PlayerSummaryOut):
    competition: str
    team: str | None
    value: float
    goals: int
    shots: int


class PartnershipOut(BaseModel):
    scorer: PlayerSummaryOut
    assister_name: str
    assister: PlayerSummaryOut | None
    team: str
    competition: str
    goals: int


class PlayerShotOut(BaseModel):
    minute: int
    result: str
    x: float
    y: float
    xg: float
    situation: str
    shot_type: str
    decisive: bool
    assisted_by: str | None
    competition: str
    season_label: str
    team: str
    opponent: str
    played_on: date


class ShotIngestionSummaryOut(BaseModel):
    matches: int
    shots: int
    remaining: int


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
        birth_year=player.birth_year,
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
        minutes_played=statistics.minutes_played,
        expected_assists=statistics.expected_assists,
        xg_chain=statistics.xg_chain,
        xg_buildup=statistics.xg_buildup,
    )


def season_out_from_domain(season: Season, team: str | None = None) -> SeasonOut:
    return SeasonOut(competition=season.competition, label=season.label, team=team)


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


def season_leader_out_from_domain(leader: SeasonRecord) -> SeasonLeaderOut:
    return SeasonLeaderOut(
        **player_out_from_domain(leader.player, leader.statistics).model_dump(),
        competition=leader.season.competition,
        season_label=leader.season.label,
        team=leader.team,
    )


def percentile_report_out_from_domain(report: PercentileReport) -> PercentileReportOut:
    return PercentileReportOut(
        competition=report.season.competition,
        season_label=report.season.label,
        position=report.position,
        peer_count=report.peer_count,
        minimum_minutes=report.minimum_minutes,
        metrics={
            metric: MetricPercentileOut(
                per_90=value.per_90, percentile=value.percentile
            )
            for metric, value in report.metrics.items()
        },
    )


def _twin_profile_fields(profile: TwinProfile) -> dict:
    return {
        **player_summary_from_domain(profile.player).model_dump(),
        "competition": profile.season.competition,
        "season_label": profile.season.label,
        "team": profile.team,
        "market_value_eur": (
            profile.market_value.amount_eur if profile.market_value else None
        ),
        "percentiles": {
            metric: value.percentile for metric, value in profile.percentiles.items()
        },
    }


def twin_report_out_from_domain(report: TwinReport) -> TwinReportOut:
    return TwinReportOut(
        target=TwinProfileOut(**_twin_profile_fields(report.target)),
        twins=[
            TwinOut(
                **_twin_profile_fields(twin),
                similarity=twin.similarity,
                shared_strengths=list(twin.shared_strengths),
                differences=list(twin.differences),
            )
            for twin in report.twins
        ],
    )


def shot_leader_out_from_domain(leader: ShotLeader) -> ShotLeaderOut:
    return ShotLeaderOut(
        **player_summary_from_domain(leader.player).model_dump(),
        competition=leader.competition,
        team=leader.team,
        value=round(leader.value, 2),
        goals=leader.goals,
        shots=leader.shots,
    )


def partnership_out_from_domain(pair: Partnership) -> PartnershipOut:
    return PartnershipOut(
        scorer=player_summary_from_domain(pair.scorer),
        assister_name=pair.assister_name,
        assister=player_summary_from_domain(pair.assister) if pair.assister else None,
        team=pair.team,
        competition=pair.competition,
        goals=pair.goals,
    )


def player_shot_out_from_domain(entry: PlayerShot) -> PlayerShotOut:
    shot = entry.shot
    return PlayerShotOut(
        minute=shot.minute,
        result=shot.result,
        x=round(shot.x, 3),
        y=round(shot.y, 3),
        xg=round(shot.xg, 3),
        situation=shot.situation,
        shot_type=shot.shot_type,
        decisive=shot.decisive,
        assisted_by=shot.assisted_by,
        competition=entry.competition,
        season_label=entry.season_label,
        team=entry.team,
        opponent=entry.opponent,
        played_on=entry.played_on,
    )
