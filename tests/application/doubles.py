from __future__ import annotations

from dataclasses import replace
from datetime import date

from player_scouting.application.league_ingestion_job import LeagueIngestionJob
from player_scouting.application.ports import (
    AdvancedSeasonRow,
    CompetitionStatisticsResult,
    EnrichmentUnavailableError,
    LeaderMetric,
    LeaguePlayersPage,
    LeagueSummary,
    MarketValueHistoryResult,
    MatchRef,
    PlayerSeasonResult,
    PlayerSort,
    PlayerSummary,
    SeasonEntry,
    SeasonRecord,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.shots import Shot
from player_scouting.domain.statistics import AdvancedStatistics, Statistics


class InMemoryPlayerRepository:
    def __init__(self) -> None:
        self._players: dict[int, Player] = {}
        self._season_statistics: dict[tuple[int, Season], Statistics] = {}
        self._market_value_history: dict[int, list[MarketValuePoint]] = {}
        self._teams: dict[tuple[int, Season], str | None] = {}
        self._advanced: dict[tuple[int, Season], AdvancedStatistics] = {}
        self._understat_ids: dict[int, int] = {}
        self._enrichment_checked: set[int] = set()

    def add(self, player: Player, season: Season, statistics: Statistics) -> None:
        self.save_player(player)
        self.save_season_statistics(player.player_id, season, statistics)

    def get_player(self, player_id: int) -> Player | None:
        return self._players.get(player_id)

    def list_players(self) -> list[Player]:
        return list(self._players.values())

    def search_player_summaries(
        self, query: str | None, sort: PlayerSort, limit: int
    ) -> list[PlayerSummary]:
        summaries = []
        for player in self._players.values():
            if query and query.lower() not in player.name.lower():
                continue
            years = [
                season.start_year
                for (player_id, season) in self._season_statistics
                if player_id == player.player_id and season.start_year is not None
            ]
            summaries.append(
                PlayerSummary(
                    player,
                    self.get_career_statistics(player.player_id),
                    max(years) if years else None,
                )
            )

        def sort_key(summary: PlayerSummary) -> tuple:
            career = summary.career
            if sort == "goals":
                return (-career.goals, summary.player.name)
            if sort == "assists":
                return (-career.assists, summary.player.name)
            return (
                summary.latest_season_year is None,
                -(summary.latest_season_year or 0),
                -(career.goals + career.assists),
                summary.player.name,
            )

        return sorted(summaries, key=sort_key)[:limit]

    def save_player(self, player: Player) -> None:
        self._players[player.player_id] = player

    def save_season_statistics(
        self,
        player_id: int,
        season: Season,
        statistics: Statistics,
        team: str | None = None,
    ) -> None:
        self._season_statistics[(player_id, season)] = statistics
        self._teams[(player_id, season)] = team

    def save_season_advanced(
        self, player_id: int, season: Season, advanced: AdvancedStatistics
    ) -> None:
        self._advanced[(player_id, season)] = advanced

    def _merged(self, player_id: int, season: Season) -> Statistics:
        statistics = self._season_statistics[(player_id, season)]
        advanced = self._advanced.get((player_id, season))
        return statistics.with_advanced(advanced) if advanced else statistics

    def get_season_statistics(
        self, player_id: int, season: Season
    ) -> Statistics | None:
        if (player_id, season) not in self._season_statistics:
            return None
        return self._merged(player_id, season)

    def list_season_leaders(
        self,
        season_label: str,
        metric: LeaderMetric,
        limit: int,
        competition: str | None = None,
    ) -> list[SeasonRecord]:
        leaders = [
            SeasonRecord(
                self._players[player_id],
                season,
                self._teams.get((player_id, season)),
                self._merged(player_id, season),
            )
            for (player_id, season) in self._season_statistics
            if season.label == season_label
            and competition in (None, season.competition)
            and player_id in self._players
        ]
        leaders.sort(
            key=lambda leader: (-getattr(leader.statistics, metric), leader.player.name)
        )
        return leaders[:limit]

    def list_season_records(self, season_labels: list[str]) -> list[SeasonRecord]:
        return [
            SeasonRecord(
                self._players[player_id],
                season,
                self._teams.get((player_id, season)),
                self._merged(player_id, season),
            )
            for (player_id, season) in self._season_statistics
            if season.label in season_labels and player_id in self._players
        ]

    def latest_market_values(self) -> dict[int, MarketValuePoint]:
        return {
            player_id: max(points, key=lambda point: point.as_of)
            for player_id, points in self._market_value_history.items()
            if points
        }

    def list_season_entries(self, season: Season) -> list[SeasonEntry]:
        return [
            SeasonEntry(
                self._players[player_id],
                self._teams.get((player_id, entry_season)),
                self._merged(player_id, entry_season),
            )
            for (player_id, entry_season) in self._season_statistics
            if entry_season == season and player_id in self._players
        ]

    def set_understat_id(self, player_id: int, understat_id: int) -> None:
        self._understat_ids[player_id] = understat_id

    def understat_id_of(self, player_id: int) -> int | None:
        return self._understat_ids.get(player_id)

    def list_players_pending_enrichment(self, limit: int) -> list[Player]:
        ranked = self.search_player_summaries(None, "recent", len(self._players))
        pending = [
            s.player
            for s in ranked
            if s.player.player_id not in self._enrichment_checked
        ]
        return pending[:limit]

    def mark_enrichment_checked(self, player_id: int) -> None:
        self._enrichment_checked.add(player_id)

    def is_enrichment_checked(self, player_id: int) -> bool:
        return player_id in self._enrichment_checked

    def get_season_team(self, player_id: int, season: Season) -> str | None:
        return self._teams.get((player_id, season))

    def list_seasons_for_player(self, player_id: int) -> list[Season]:
        return [season for (pid, season) in self._season_statistics if pid == player_id]

    def get_career_statistics(self, player_id: int) -> Statistics:
        stats = [
            self._merged(pid, season)
            for (pid, season) in self._season_statistics
            if pid == player_id
        ]
        return sum(stats, Statistics(0, 0))

    def list_all_season_statistics(
        self,
    ) -> list[tuple[Player, Season, Statistics]]:
        entries = []
        for player_id, season in self._season_statistics:
            player = self._players.get(player_id)
            if player is not None:
                entries.append((player, season, self._merged(player_id, season)))
        return entries

    def save_market_value_history(
        self, player_id: int, points: list[MarketValuePoint]
    ) -> None:
        self._market_value_history[player_id] = list(points)

    def list_market_value_history(self, player_id: int) -> list[MarketValuePoint]:
        return self._market_value_history.get(player_id, [])


class FakeCompetitionStatisticsProvider:
    def __init__(self, result: CompetitionStatisticsResult) -> None:
        self._result = result

    def get_statistics(
        self, competition_id: int, season_id: int
    ) -> CompetitionStatisticsResult:
        return self._result


class FakeBirthDateProvider:
    def __init__(self, dates_by_name: dict[str, date | None]) -> None:
        self._dates_by_name = dates_by_name

    def find(self, name: str, nationality: str | None = None) -> date | None:
        return self._dates_by_name.get(name)


class FakePlayerSeasonStatisticsProvider:
    def __init__(self, result: PlayerSeasonResult | None) -> None:
        self._result = result

    def get_player_statistics(
        self, player_name: str, league_id: int, season_year: int
    ) -> PlayerSeasonResult | None:
        return self._result


class FakeSeasonDatasetProvider:
    def __init__(self, seasons: dict[int, list[PlayerSeasonResult]]) -> None:
        self._seasons = seasons

    def get_season(self, start_year: int) -> list[PlayerSeasonResult]:
        return self._seasons[start_year]


class FakeMarketValueProvider:
    def __init__(
        self,
        result: MarketValueHistoryResult | None = None,
        results_by_name: dict[str, MarketValueHistoryResult] | None = None,
        blocked_after: int | None = None,
    ) -> None:
        self._result = result
        self._results_by_name = results_by_name
        self._blocked_after = blocked_after
        self.requests: list[tuple[str, int | None]] = []

    def get_market_value_history(
        self, player_name: str, birth_year: int | None = None
    ) -> MarketValueHistoryResult | None:
        if (
            self._blocked_after is not None
            and len(self.requests) >= self._blocked_after
        ):
            raise EnrichmentUnavailableError("blocked")
        self.requests.append((player_name, birth_year))
        if self._results_by_name is not None:
            return self._results_by_name.get(player_name)
        return self._result


class FakeLeaguePlayersProvider:
    def __init__(self, pages: dict[tuple[int, int], list[LeaguePlayersPage]]) -> None:
        self._pages = pages
        self.requested_pages: list[tuple[int, int, int]] = []

    def get_players_page(
        self, league_id: int, season_year: int, page: int
    ) -> LeaguePlayersPage:
        self.requested_pages.append((league_id, season_year, page))
        return self._pages[(league_id, season_year)][page - 1]


class FakeLeagueSearchProvider:
    def __init__(self, results: list[LeagueSummary]) -> None:
        self._results = results

    def search_leagues(self, query: str) -> list[LeagueSummary]:
        return self._results


class InMemoryLeagueIngestionJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[int, LeagueIngestionJob] = {}
        self._next_id = 1

    def save_job(self, job: LeagueIngestionJob) -> LeagueIngestionJob:
        if job.id is None:
            job = replace(job, id=self._next_id)
            self._next_id += 1
        self._jobs[job.id] = job
        return job

    def get_job(self, job_id: int) -> LeagueIngestionJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[LeagueIngestionJob]:
        return list(self._jobs.values())

    def next_pending_job(self) -> LeagueIngestionJob | None:
        for job in self._jobs.values():
            if not job.is_completed:
                return job
        return None


class FakeAdvancedSeasonProvider:
    def __init__(self, seasons: dict[int, list[AdvancedSeasonRow]]) -> None:
        self._seasons = seasons

    def get_season(self, start_year: int) -> list[AdvancedSeasonRow]:
        return self._seasons[start_year]


class FakeShotProvider:
    def __init__(self, matches: list[MatchRef], shots: dict[int, list[Shot]]) -> None:
        self._matches = matches
        self._shots = shots
        self.requested: list[int] = []

    def list_played_matches(self, start_year: int) -> list[MatchRef]:
        return list(self._matches)

    def get_match_shots(self, match: MatchRef) -> list[Shot]:
        self.requested.append(match.match_id)
        return list(self._shots[match.match_id])


class InMemoryShotRepository:
    def __init__(self) -> None:
        self._matches: dict[int, MatchRef] = {}
        self._shots: dict[int, list[Shot]] = {}

    def known_match_ids(self, season_label: str) -> set[int]:
        return {
            match_id
            for match_id, match in self._matches.items()
            if match.season_label == season_label
        }

    def save_match(self, match: MatchRef, shots: list[Shot]) -> None:
        self._matches[match.match_id] = match
        self._shots[match.match_id] = list(shots)

    def shots_of(self, match_id: int) -> list[Shot]:
        return self._shots[match_id]
