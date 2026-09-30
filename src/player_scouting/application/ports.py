from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Protocol

from player_scouting.application.player_matching import ExternalPlayer
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.shots import Shot, ShotTotals
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

    def list_duplicate_groups(self) -> list[list[int]]: ...

    def find_by_understat_ids(self, understat_ids: list[int]) -> dict[int, Player]: ...

    def set_transfermarkt_id(self, player_id: int, transfermarkt_id: int) -> None: ...

    def transfermarkt_index(self) -> dict[int, int]:
        """Transfermarkt id -> our player id."""
        ...

    def merge_players(self, keep: int, remove: int) -> None: ...

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


@dataclass(frozen=True)
class MatchRef:
    match_id: int
    competition: str
    season_label: str
    played_on: date
    home_team: str
    away_team: str


class ShotProvider(Protocol):
    def list_played_matches(self, start_year: int) -> list[MatchRef]: ...

    def get_match_shots(self, match: MatchRef) -> list[Shot]: ...

    def get_match_rosters(self, match: MatchRef) -> list[RosterEntry]: ...


ShotMetric = Literal[
    "late_goals",
    "decisive_goals",
    "late_decisive_goals",
    "headed_goals",
    "outside_box_goals",
    "set_piece_goals",
    "finishing",
    "npxg_per_shot",
]


@dataclass(frozen=True)
class ShotLeader:
    player: Player
    competition: str
    team: str | None
    value: float
    goals: int
    shots: int


@dataclass(frozen=True)
class PlayerShot:
    shot: Shot
    competition: str
    season_label: str
    team: str
    opponent: str
    played_on: date


@dataclass(frozen=True)
class Partnership:
    scorer: Player
    assister_name: str
    assister: Player | None
    team: str
    competition: str
    goals: int


class ShotRepository(Protocol):
    def known_match_ids(self, season_label: str) -> set[int]: ...

    def save_match(self, match: MatchRef, shots: list[Shot]) -> None: ...

    def list_shot_leaders(
        self,
        season_label: str,
        metric: ShotMetric,
        limit: int,
        competition: str | None = None,
    ) -> list[ShotLeader]: ...

    def list_player_shots(
        self, player_id: int, season_label: str | None = None
    ) -> list[PlayerShot]: ...

    def list_partnerships(
        self, season_label: str, limit: int, competition: str | None = None
    ) -> list[Partnership]: ...

    def list_shot_totals(
        self, season_labels: list[str]
    ) -> dict[tuple[int, Season], ShotTotals]: ...

    def save_rosters(self, match_id: int, entries: list[RosterEntry]) -> None: ...

    def list_rosters(
        self, competition: str, season_labels: list[str]
    ) -> list[RosterEntry]: ...

    def matches_without_rosters(
        self, season_label: str, limit: int
    ) -> list[MatchRef]: ...

    def list_team_players(self, season_label: str, team: str) -> list[ShotLeader]:
        """The team's shooters, by goals then expected goals (value = xG)."""
        ...


@dataclass(frozen=True)
class DatasetProfile:
    """A player as the public Transfermarkt dataset describes him."""

    transfermarkt_id: int
    name: str
    date_of_birth: date | None
    position: str
    detailed_position: str | None
    foot: str | None
    height_cm: int | None
    photo_url: str | None
    club: str | None
    valuations: tuple[MarketValuePoint, ...]


@dataclass(frozen=True)
class DatasetSeasonRow:
    transfermarkt_id: int
    competition: str
    season_label: str
    team: str | None
    statistics: Statistics


class TransfermarktDatasetProvider(Protocol):
    def profiles(self) -> list[DatasetProfile]: ...

    def season_rows(self, start_year: int) -> list[DatasetSeasonRow]:
        """League seasons outside the five big leagues (those come from FBref)."""
        ...


@dataclass(frozen=True)
class Fixture:
    match_id: int
    competition: str
    season_label: str
    kickoff: datetime
    home_team: str
    away_team: str
    home_goals: int | None
    away_goals: int | None
    home_xg: float | None
    away_xg: float | None

    @property
    def played(self) -> bool:
        return self.home_goals is not None and self.away_goals is not None


@dataclass(frozen=True)
class TeamMatch:
    """A played match from one team's side, with Understat's team metrics."""

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
    npxg_for: float
    npxg_against: float
    # Passes allowed per defensive action: lower = more intense pressing.
    ppda: float | None
    ppda_allowed: float | None
    deep: int
    deep_allowed: int
    xpts: float
    result: str


class TeamDataProvider(Protocol):
    def get_team_season(
        self, start_year: int
    ) -> tuple[list[Fixture], list[TeamMatch]]: ...


class TeamRepository(Protocol):
    def save_team_season(
        self, fixtures: list[Fixture], team_matches: list[TeamMatch]
    ) -> None: ...

    def list_team_matches(
        self, season_labels: list[str], competition: str | None = None
    ) -> list[TeamMatch]: ...

    def list_fixtures(
        self,
        competition: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Fixture]: ...


@dataclass(frozen=True)
class MatchStats:
    """One match as football-data.co.uk records it: stats (once played) and odds."""

    competition: str
    season_label: str
    played_on: date
    home_team: str
    away_team: str
    referee: str | None
    home_goals: int | None = None
    away_goals: int | None = None
    home_goals_ht: int | None = None
    away_goals_ht: int | None = None
    home_shots: int | None = None
    away_shots: int | None = None
    home_shots_on_target: int | None = None
    away_shots_on_target: int | None = None
    home_fouls: int | None = None
    away_fouls: int | None = None
    home_corners: int | None = None
    away_corners: int | None = None
    home_yellows: int | None = None
    away_yellows: int | None = None
    home_reds: int | None = None
    away_reds: int | None = None
    odds_home: float | None = None
    odds_draw: float | None = None
    odds_away: float | None = None
    odds_over_2_5: float | None = None
    odds_under_2_5: float | None = None

    @property
    def played(self) -> bool:
        return self.home_goals is not None and self.away_goals is not None


class MatchStatsProvider(Protocol):
    def season(self, start_year: int) -> list[MatchStats]: ...

    def upcoming(self) -> list[MatchStats]: ...


class MatchStatsRepository(Protocol):
    def save_match_stats(self, matches: list[MatchStats]) -> None: ...

    def list_match_stats(
        self, competition: str, season_labels: list[str]
    ) -> list[MatchStats]: ...

    def find_upcoming(
        self, competition: str, played_on: date, home_team: str, away_team: str
    ) -> MatchStats | None: ...


@dataclass(frozen=True)
class RosterEntry:
    """One player's line in one match (Understat roster)."""

    match_id: int
    competition: str
    season_label: str
    played_on: date
    team: str
    opponent: str
    home: bool
    understat_player_id: int
    player_name: str
    position: str
    minutes: int
    goals: int
    own_goals: int
    assists: int
    shots: int
    key_passes: int
    xg: float
    xa: float
    yellow: int
    red: int
