from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics


class PlayerRepository(Protocol):
    def get_player(self, player_id: int) -> Player | None: ...

    def list_players(self) -> list[Player]: ...

    def save_player(self, player: Player) -> None: ...

    def save_season_statistics(
        self, player_id: int, season: Season, statistics: Statistics
    ) -> None: ...

    def get_season_statistics(
        self, player_id: int, season: Season
    ) -> Statistics | None: ...

    def list_seasons_for_player(self, player_id: int) -> list[Season]: ...

    def get_career_statistics(self, player_id: int) -> Statistics: ...

    def list_all_season_statistics(
        self,
    ) -> list[tuple[Player, Season, Statistics]]: ...


class BirthDateProvider(Protocol):
    def find(self, name: str, nationality: str | None = None) -> date | None: ...


@dataclass
class PlayerCompetitionStats:
    player_id: int
    name: str
    position: str | None
    nationality: str | None
    goals: int
    assists: int
    shots: int = 0
    shots_on_target: int = 0
    expected_goals: float = 0.0
    passes_completed: int = 0
    passes_attempted: int = 0
    key_passes: int = 0
    dribbles_completed: int = 0
    dribbles_attempted: int = 0
    tackles_won: int = 0
    interceptions: int = 0
    fouls_committed: int = 0
    fouls_won: int = 0
    yellow_cards: int = 0
    red_cards: int = 0


@dataclass
class CompetitionStatisticsResult:
    season: Season
    players: list[PlayerCompetitionStats]


class CompetitionStatisticsProvider(Protocol):
    def get_statistics(
        self, competition_id: int, season_id: int
    ) -> CompetitionStatisticsResult: ...


@dataclass
class PlayerSeasonResult:
    player_id: int
    name: str
    position: str | None
    date_of_birth: date
    season: Season
    statistics: Statistics


class PlayerSeasonStatisticsProvider(Protocol):
    def get_player_statistics(
        self, player_name: str, league_id: int, season_year: int
    ) -> PlayerSeasonResult | None: ...
