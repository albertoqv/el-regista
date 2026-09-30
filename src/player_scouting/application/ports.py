from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal, Protocol

from player_scouting.application.player_matching import ExternalPlayer
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import AdvancedStatistics, Statistics

PlayerSort = Literal["recent", "goals", "assists"]
LeaderMetric = Literal[
    "goals",
    "assists",
    "expected_goals",
    "expected_assists",
    "shots",
    "key_passes",
    "xg_chain",
    "dribbles_completed",
    "tackles_won",
    "interceptions",
]


@dataclass
class SeasonEntry:
    player: Player
    team: str | None
    statistics: Statistics


@dataclass
class SeasonRecord:
    player: Player
    season: Season
    team: str | None
    statistics: Statistics


@dataclass
class PlayerSummary:
    player: Player
    career: Statistics
    latest_season_year: int | None


class PlayerRepository(Protocol):
    def get_player(self, player_id: int) -> Player | None: ...

    def list_players(self) -> list[Player]: ...

    def search_player_summaries(
        self, query: str | None, sort: PlayerSort, limit: int
    ) -> list[PlayerSummary]: ...

    def list_season_leaders(
        self,
        season_label: str,
        metric: LeaderMetric,
        limit: int,
        competition: str | None = None,
    ) -> list[SeasonRecord]: ...

    def list_season_records(self, season_labels: list[str]) -> list[SeasonRecord]: ...

    def latest_market_values(self) -> dict[int, MarketValuePoint]: ...

    def save_player(self, player: Player) -> None: ...

    def save_season_statistics(
        self,
        player_id: int,
        season: Season,
        statistics: Statistics,
        team: str | None = None,
    ) -> None: ...

    def save_season_advanced(
        self, player_id: int, season: Season, advanced: AdvancedStatistics
    ) -> None: ...

    def list_season_entries(self, season: Season) -> list[SeasonEntry]: ...

    def set_understat_id(self, player_id: int, understat_id: int) -> None: ...

    def list_players_pending_enrichment(self, limit: int) -> list[Player]: ...

    def mark_enrichment_checked(self, player_id: int) -> None: ...

    def get_season_statistics(
        self, player_id: int, season: Season
    ) -> Statistics | None: ...

    def list_seasons_for_player(self, player_id: int) -> list[Season]: ...

    def get_season_team(self, player_id: int, season: Season) -> str | None: ...

    def get_career_statistics(self, player_id: int) -> Statistics: ...

    def list_all_season_statistics(
        self,
    ) -> list[tuple[Player, Season, Statistics]]: ...

    def save_market_value_history(
        self, player_id: int, points: list[MarketValuePoint]
    ) -> None: ...

    def list_market_value_history(self, player_id: int) -> list[MarketValuePoint]: ...


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
    date_of_birth: date | None
    season: Season
    statistics: Statistics
    photo_url: str | None = None
    birth_year: int | None = None
    team: str | None = None


class PlayerSeasonStatisticsProvider(Protocol):
    def get_player_statistics(
        self, player_name: str, league_id: int, season_year: int
    ) -> PlayerSeasonResult | None: ...


class SeasonDatasetProvider(Protocol):
    def get_season(self, start_year: int) -> list[PlayerSeasonResult]: ...


@dataclass
class AdvancedSeasonRow:
    competition: str
    player: ExternalPlayer
    advanced: AdvancedStatistics


class AdvancedSeasonProvider(Protocol):
    def get_season(self, start_year: int) -> list[AdvancedSeasonRow]: ...


@dataclass
class MarketValueHistoryResult:
    preferred_foot: str | None
    points: list[MarketValuePoint]
    photo_url: str | None = None
    date_of_birth: date | None = None


class EnrichmentUnavailableError(Exception):
    """The enrichment source is blocking or down; stop instead of skipping players."""


class MarketValueProvider(Protocol):
    def get_market_value_history(
        self, player_name: str, birth_year: int | None = None
    ) -> MarketValueHistoryResult | None: ...


@dataclass
class LeaguePlayersPage:
    players: list[PlayerSeasonResult]
    current_page: int
    total_pages: int


class LeaguePageUnavailableError(Exception):
    """Raised when the provider cannot serve a given page (e.g. a plan limit)."""


class LeaguePlayersProvider(Protocol):
    def get_players_page(
        self, league_id: int, season_year: int, page: int
    ) -> LeaguePlayersPage:
        """May raise LeaguePageUnavailableError if this page cannot be served."""
        ...


@dataclass
class LeagueSummary:
    id: int
    name: str
    country: str


class LeagueSearchProvider(Protocol):
    def search_leagues(self, query: str) -> list[LeagueSummary]: ...
