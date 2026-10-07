"""Estimates every player's market value from his last finished season.

Runs in the refresh (twice a week): reads players, their latest Transfermarkt value
and their competition lines once, fits the model and stores one estimate per player.
The web only reads each player's stored row.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from player_scouting.application.ports import (
    CompetitionStatsRepository,
    PlayerRepository,
    ValueEstimateRepository,
)
from player_scouting.domain.career import MINIMUM_MINUTES
from player_scouting.domain.competitions import CompetitionLine
from player_scouting.domain.entities import Player
from player_scouting.domain.valuation import ValuationInput, estimate_values


@dataclass(frozen=True)
class ValuationResult:
    estimated: int
    samples: int
    median_error: float


def _last_finished_season(today: date) -> int:
    current = today.year if today.month >= 7 else today.year - 1
    return current - 1


def _age(player: Player, today: date) -> float | None:
    if player.date_of_birth:
        return (today - player.date_of_birth).days / 365.25
    if player.birth_year:
        return today.year - player.birth_year
    return None


def _input(
    player: Player,
    lines: list[CompetitionLine],
    season: int,
    value: int | None,
    today: date,
) -> ValuationInput | None:
    age = _age(player, today)
    club = [
        line
        for line in lines
        if line.kind != "national" and line.season_label == str(season)
    ]
    minutes = sum(line.minutes_played for line in club)
    if age is None or minutes < MINIMUM_MINUTES:
        return None
    leagues = [line for line in club if line.kind == "league"]
    league = max(leagues, key=lambda line: line.minutes_played) if leagues else None
    return ValuationInput(
        player_id=player.player_id,
        age=age,
        position=player.position,
        league=league.competition if league else None,
        minutes=minutes,
        goals_per90=sum(line.goals for line in club) * 90 / minutes,
        assists_per90=sum(line.assists for line in club) * 90 / minutes,
        europe_appearances=sum(
            line.appearances for line in club if line.kind == "continental"
        ),
        # The last two seasons with his national team (tournaments carry their year).
        national_appearances=sum(
            line.appearances
            for line in lines
            if line.kind == "national" and int(line.season_label) >= season
        ),
        market_value_eur=value,
    )


@dataclass
class EstimateMarketValuesUseCase:
    players: PlayerRepository
    competitions: CompetitionStatsRepository
    estimates: ValueEstimateRepository
    today: Callable[[], date] = field(default=date.today)

    def execute(self) -> ValuationResult:
        today = self.today()
        season = _last_finished_season(today)
        lines = self.competitions.list_competition_lines_since(str(season))
        values = self.players.latest_market_values()
        inputs = [
            item
            for player in self.players.list_players()
            if (
                item := _input(
                    player,
                    lines.get(player.player_id, []),
                    season,
                    values[player.player_id].amount_eur
                    if player.player_id in values
                    else None,
                    today,
                )
            )
        ]
        report = estimate_values(inputs)
        self.estimates.save_value_estimates(report, today)
        return ValuationResult(
            estimated=len(report.estimates),
            samples=report.samples,
            median_error=report.median_error,
        )
