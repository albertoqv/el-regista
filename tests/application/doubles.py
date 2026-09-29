from __future__ import annotations

from dataclasses import replace
from datetime import date

from player_scouting.application.league_ingestion_job import LeagueIngestionJob
from player_scouting.application.ports import (
    CompetitionStatisticsResult,
    LeaguePlayersPage,
    LeagueSummary,
    MarketValueHistoryResult,
    PlayerSeasonResult,
    PlayerSort,
    PlayerSummary,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics


class InMemoryPlayerRepository:
    def __init__(self) -> None:
        self._players: dict[int, Player] = {}
        self._season_statistics: dict[tuple[int, Season], Statistics] = {}
        self._market_value_history: dict[int, list[MarketValuePoint]] = {}

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
        self, player_id: int, season: Season, statistics: Statistics
    ) -> None:
        self._season_statistics[(player_id, season)] = statistics

    def get_season_statistics(
        self, player_id: int, season: Season
    ) -> Statistics | None:
        return self._season_statistics.get((player_id, season))

    def list_seasons_for_player(self, player_id: int) -> list[Season]:
        return [season for (pid, season) in self._season_statistics if pid == player_id]

    def get_career_statistics(self, player_id: int) -> Statistics:
        stats = [
            statistics
            for (pid, _), statistics in self._season_statistics.items()
            if pid == player_id
        ]
        return sum(stats, Statistics(0, 0))

    def list_all_season_statistics(
        self,
    ) -> list[tuple[Player, Season, Statistics]]:
        entries = []
        for (player_id, season), statistics in self._season_statistics.items():
            player = self._players.get(player_id)
            if player is not None:
                entries.append((player, season, statistics))
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
    def __init__(self, result: MarketValueHistoryResult | None) -> None:
        self._result = result

    def get_market_value_history(
        self, player_name: str
    ) -> MarketValueHistoryResult | None:
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
