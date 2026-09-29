from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from player_scouting.application.use_cases.ingest_competition import IngestionResult
from player_scouting.domain.comparison import Comparison
from player_scouting.domain.entities import Player
from player_scouting.domain.statistics import Statistics


class PlayerSummaryOut(BaseModel):
    player_id: int
    name: str
    position: str
    date_of_birth: date


class PlayerOut(PlayerSummaryOut):
    goals: int
    assists: int


class ComparisonOut(BaseModel):
    player1: PlayerSummaryOut
    player2: PlayerSummaryOut
    similarity_percentage: int


class SkippedPlayerOut(BaseModel):
    player_id: int
    name: str
    reason: str


class IngestionResultOut(BaseModel):
    ingested: int
    skipped: list[SkippedPlayerOut]


def player_summary_from_domain(player: Player) -> PlayerSummaryOut:
    return PlayerSummaryOut(
        player_id=player.player_id,
        name=player.name,
        position=player.position,
        date_of_birth=player.date_of_birth,
    )


def player_out_from_domain(player: Player, statistics: Statistics) -> PlayerOut:
    return PlayerOut(
        **player_summary_from_domain(player).model_dump(),
        goals=statistics.goals,
        assists=statistics.assists,
    )


def comparison_out_from_domain(comparison: Comparison) -> ComparisonOut:
    return ComparisonOut(
        player1=player_summary_from_domain(comparison.player1),
        player2=player_summary_from_domain(comparison.player2),
        similarity_percentage=comparison.similarity_score.percentage,
    )


def ingestion_result_out_from_domain(result: IngestionResult) -> IngestionResultOut:
    return IngestionResultOut(
        ingested=result.ingested,
        skipped=[
            SkippedPlayerOut(player_id=s.player_id, name=s.name, reason=s.reason)
            for s in result.skipped
        ],
    )
