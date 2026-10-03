from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from player_scouting.application.ingestion_result import IngestionResult
from player_scouting.application.league_ingestion_job import LeagueIngestionJob
from player_scouting.application.ports import (
    LeagueSummary,
    Partnership,
    PlayerShot,
    ScrapedSeasonRow,
    SeasonRecord,
    ShotLeader,
    TeamMatch,
)
from player_scouting.application.use_cases.explore_players import ExploreRow
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
from player_scouting.application.use_cases.team_analytics import (
    BacktestReport,
    FixtureForecast,
    TableRow,
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
    height_cm: int | None = None
    detailed_position: str | None = None


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
    # "same", "similar" or "different" detailed role; null when unknown.
    role_match: str | None = None
    shared_strengths: list[str]
    differences: list[str]


class TwinReportOut(BaseModel):
    target: TwinProfileOut
    twins: list[TwinOut]
    basic: bool = False


class PendingEnrichmentOut(BaseModel):
    player_id: int
    name: str
    birth_year: int | None


class MarketValuePointIn(BaseModel):
    as_of: date
    amount_eur: int
    club: str


class ScrapedSeasonRowIn(BaseModel):
    transfermarkt_id: int
    name: str
    position: str
    detailed_position: str | None = None
    team: str
    goals: int = 0
    assists: int = 0
    minutes_played: int = 0
    yellow_cards: int = 0
    red_cards: int = 0

    def to_domain(self) -> ScrapedSeasonRow:
        return ScrapedSeasonRow(
            transfermarkt_id=self.transfermarkt_id,
            name=self.name,
            position=self.position,
            detailed_position=self.detailed_position,
            team=self.team,
            statistics=Statistics(
                goals=self.goals,
                assists=self.assists,
                minutes_played=self.minutes_played,
                yellow_cards=self.yellow_cards,
                red_cards=self.red_cards,
            ),
        )


class ScrapedLeagueSeasonIn(BaseModel):
    competition: str
    season_label: str
    rows: list[ScrapedSeasonRowIn]


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


class ExploreRowOut(SeasonLeaderOut):
    market_value_eur: int | None
    age: int | None
    sort_value: float


class TableRowOut(BaseModel):
    position: int
    team: str
    competition: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    points: int
    xg_for: float
    xg_against: float
    npxg_difference: float
    xpts: float
    ppda: float | None
    ppda_allowed: float | None
    deep: int
    deep_allowed: int
    form: list[str]


class TeamMatchOut(BaseModel):
    match_id: int
    competition: str
    season_label: str
    played_on: date
    team: str
    opponent: str
    home: bool
    goals_for: int
    goals_against: int
    xg_for: float
    xg_against: float
    ppda: float | None
    deep: int
    deep_allowed: int
    xpts: float
    result: str


class ScorelineOut(BaseModel):
    home: int
    away: int
    probability: float


class FixtureForecastOut(BaseModel):
    match_id: int
    competition: str
    kickoff: datetime
    home_team: str
    away_team: str
    home_win: float
    draw: float
    away_win: float
    expected_home: float
    expected_away: float
    scorelines: list[ScorelineOut]
    over_2_5: float
    both_teams_score: float
    home_form: list[str]
    away_form: list[str]


class CalibrationBucketOut(BaseModel):
    predicted: float
    observed: float
    count: int


class BacktestReportOut(BaseModel):
    matches: int
    accuracy: float
    brier: float
    log_loss: float
    baseline_accuracy: float
    baseline_brier: float
    calibration: list[CalibrationBucketOut]


class TeamSeasonSummaryOut(BaseModel):
    fixtures: int
    team_matches: int


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
        height_cm=player.height_cm,
        detailed_position=player.detailed_position,
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
                role_match=twin.role_match,
                shared_strengths=list(twin.shared_strengths),
                differences=list(twin.differences),
            )
            for twin in report.twins
        ],
        basic=report.basic,
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


def explore_row_out_from_domain(row: ExploreRow) -> ExploreRowOut:
    return ExploreRowOut(
        **season_leader_out_from_domain(row.record).model_dump(),
        market_value_eur=row.market_value.amount_eur if row.market_value else None,
        age=row.age,
        sort_value=round(row.sort_value, 2),
    )


def table_row_out_from_domain(row: TableRow, position: int) -> TableRowOut:
    return TableRowOut(
        position=position,
        team=row.team,
        competition=row.competition,
        played=row.played,
        wins=row.wins,
        draws=row.draws,
        losses=row.losses,
        goals_for=row.goals_for,
        goals_against=row.goals_against,
        points=row.points,
        xg_for=round(row.xg_for, 2),
        xg_against=round(row.xg_against, 2),
        npxg_difference=round(row.npxg_difference, 2),
        xpts=round(row.xpts, 2),
        ppda=round(row.ppda, 2) if row.ppda is not None else None,
        ppda_allowed=round(row.ppda_allowed, 2)
        if row.ppda_allowed is not None
        else None,
        deep=row.deep,
        deep_allowed=row.deep_allowed,
        form=row.form,
    )


def team_match_out_from_domain(match: TeamMatch) -> TeamMatchOut:
    return TeamMatchOut(
        match_id=match.match_id,
        competition=match.competition,
        season_label=match.season_label,
        played_on=match.played_on,
        team=match.team,
        opponent=match.opponent,
        home=match.home,
        goals_for=match.goals_for,
        goals_against=match.goals_against,
        xg_for=round(match.xg_for, 2),
        xg_against=round(match.xg_against, 2),
        ppda=round(match.ppda, 2) if match.ppda is not None else None,
        deep=match.deep,
        deep_allowed=match.deep_allowed,
        xpts=round(match.xpts, 2),
        result=match.result,
    )


def fixture_forecast_out_from_domain(forecast: FixtureForecast) -> FixtureForecastOut:
    fixture, prediction = forecast.fixture, forecast.prediction
    return FixtureForecastOut(
        match_id=fixture.match_id,
        competition=fixture.competition,
        kickoff=fixture.kickoff,
        home_team=fixture.home_team,
        away_team=fixture.away_team,
        home_win=round(prediction.home_win, 4),
        draw=round(prediction.draw, 4),
        away_win=round(prediction.away_win, 4),
        expected_home=round(prediction.expected_home, 2),
        expected_away=round(prediction.expected_away, 2),
        scorelines=[
            ScorelineOut(home=home, away=away, probability=round(probability, 4))
            for home, away, probability in prediction.scorelines
        ],
        over_2_5=round(prediction.over_2_5, 4),
        both_teams_score=round(prediction.both_teams_score, 4),
        home_form=forecast.home_form,
        away_form=forecast.away_form,
    )


def backtest_report_out_from_domain(report: BacktestReport) -> BacktestReportOut:
    return BacktestReportOut(
        matches=report.matches,
        accuracy=round(report.accuracy, 4),
        brier=round(report.brier, 4),
        log_loss=round(report.log_loss, 4),
        baseline_accuracy=round(report.baseline_accuracy, 4),
        baseline_brier=round(report.baseline_brier, 4),
        calibration=[
            CalibrationBucketOut(
                predicted=round(bucket.predicted, 4),
                observed=round(bucket.observed, 4),
                count=bucket.count,
            )
            for bucket in report.calibration
        ],
    )
