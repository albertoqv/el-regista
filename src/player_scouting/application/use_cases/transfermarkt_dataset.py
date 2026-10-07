from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace

from player_scouting.application.ingestion_result import IngestionResult, SkippedPlayer
from player_scouting.application.player_matching import name_tokens
from player_scouting.application.ports import (
    DatasetProfile,
    PlayerRepository,
    ScrapedSeasonRow,
    TransfermarktDatasetProvider,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics

# Players created from the dataset get ids in their own range, far from
# StatsBomb's small ids and FBref's hashed ones (>= 1e9).
TRANSFERMARKT_ID_OFFSET = 500_000_000


def _birth_year(player: Player) -> int | None:
    if player.date_of_birth is not None:
        return player.date_of_birth.year
    return player.birth_year


class _PlayerIndex:
    """Finds our player for a dataset profile: same birth year and same name."""

    def __init__(self, players: list[Player]) -> None:
        self._by_year: dict[int, list[Player]] = defaultdict(list)
        for player in players:
            year = _birth_year(player)
            if year is not None:
                self._by_year[year].append(player)

    def find(self, profile: DatasetProfile) -> Player | None:
        if profile.date_of_birth is None:
            return None
        wanted = name_tokens(profile.name)
        same_year = self._by_year.get(profile.date_of_birth.year, [])
        exact = [p for p in same_year if name_tokens(p.name) == wanted]
        if len(exact) == 1:
            return exact[0]
        # "Vinicius Junior" vs "Vinícius Júnior Silva": one name inside the other.
        partial = [
            p
            for p in same_year
            if name_tokens(p.name) <= wanted or wanted <= name_tokens(p.name)
        ]
        if partial:
            return partial[0] if len(partial) == 1 else None
        # "Dani Carvajal" vs "Daniel Carvajal": same surname, only one that year.
        surname = profile.name.split()[-1]
        by_surname = [
            p
            for p in same_year
            if name_tokens(p.name.split()[-1]) == name_tokens(surname)
        ]
        return by_surname[0] if len(by_surname) == 1 else None


@dataclass
class EnrichFromDatasetUseCase:
    """Photos, birth dates, height, role and market values for our players."""

    provider: TransfermarktDatasetProvider
    repository: PlayerRepository

    def execute(self) -> IngestionResult:
        known = self.repository.transfermarkt_index()
        linked = set(known.values())
        players = {p.player_id: p for p in self.repository.list_players()}
        index = _PlayerIndex(
            [p for player_id, p in players.items() if player_id not in linked]
        )
        claims: dict[int, list[DatasetProfile]] = defaultdict(list)
        for profile in self.provider.profiles():
            player_id = known.get(profile.transfermarkt_id)
            if player_id is None:
                found = index.find(profile)
                player_id = found.player_id if found else None
            if player_id is not None and player_id in players:
                claims[player_id].append(profile)

        matched = 0
        for player_id, profiles in claims.items():
            # Two dataset players claiming one of ours: homonyms, trust neither.
            if len(profiles) > 1:
                continue
            [profile] = profiles
            if known.get(profile.transfermarkt_id) != player_id:
                self.repository.set_transfermarkt_id(
                    player_id, profile.transfermarkt_id
                )
            self._apply(players[player_id], profile)
            matched += 1
        return IngestionResult(ingested=matched, skipped=[])

    def _apply(self, player: Player, profile: DatasetProfile) -> None:
        self.repository.save_player(
            replace(
                player,
                photo_url=player.photo_url or profile.photo_url,
                date_of_birth=player.date_of_birth or profile.date_of_birth,
                preferred_foot=player.preferred_foot or profile.foot,
                height_cm=profile.height_cm or player.height_cm,
                detailed_position=profile.detailed_position or player.detailed_position,
            )
        )
        if not profile.valuations:
            return
        current = self.repository.list_market_value_history(player.player_id)
        newest_known = max((p.as_of for p in current), default=None)
        newest_dataset = max(p.as_of for p in profile.valuations)
        # Never replace a fresher history (e.g. one scraped this week).
        if newest_known is None or newest_dataset > newest_known:
            self.repository.save_market_value_history(
                player.player_id, sorted(profile.valuations, key=lambda p: p.as_of)
            )


@dataclass
class IngestDatasetLeaguesUseCase:
    """Seasons of the leagues FBref does not cover (Portugal, Netherlands...)."""

    provider: TransfermarktDatasetProvider
    repository: PlayerRepository

    def execute(self, start_year: int) -> IngestionResult:
        profiles = {p.transfermarkt_id: p for p in self.provider.profiles()}
        known = self.repository.transfermarkt_index()
        ingested = 0
        skipped: list[SkippedPlayer] = []
        for row in self.provider.season_rows(start_year):
            player_id = known.get(row.transfermarkt_id)
            if player_id is None:
                profile = profiles.get(row.transfermarkt_id)
                if profile is None:
                    skipped.append(
                        SkippedPlayer(
                            row.transfermarkt_id, "", "no profile in the dataset"
                        )
                    )
                    continue
                player_id = self._create(profile)
                known[row.transfermarkt_id] = player_id
            self.repository.save_season_statistics(
                player_id,
                Season(row.competition, row.season_label),
                row.statistics,
                row.team,
            )
            ingested += 1
        return IngestionResult(ingested=ingested, skipped=skipped)

    def _create(self, profile: DatasetProfile) -> int:
        return create_from_profile(self.repository, profile)


def create_from_profile(repository: PlayerRepository, profile: DatasetProfile) -> int:
    """A player we did not have, from his dataset profile (with his values)."""
    player_id = TRANSFERMARKT_ID_OFFSET + profile.transfermarkt_id
    repository.save_player(
        Player(
            player_id,
            profile.name,
            profile.position,
            profile.date_of_birth,
            photo_url=profile.photo_url,
            preferred_foot=profile.foot,
            birth_year=profile.date_of_birth.year if profile.date_of_birth else None,
            height_cm=profile.height_cm,
            detailed_position=profile.detailed_position,
        )
    )
    repository.set_transfermarkt_id(player_id, profile.transfermarkt_id)
    if profile.valuations:
        repository.save_market_value_history(
            player_id, sorted(profile.valuations, key=lambda p: p.as_of)
        )
    return player_id


def _added(first: Statistics, second: Statistics) -> Statistics:
    return replace(
        first,
        goals=first.goals + second.goals,
        assists=first.assists + second.assists,
        minutes_played=first.minutes_played + second.minutes_played,
        yellow_cards=first.yellow_cards + second.yellow_cards,
        red_cards=first.red_cards + second.red_cards,
    )


@dataclass
class IngestScrapedLeagueSeasonUseCase:
    """The season in progress of the extra leagues, which the dataset lacks.

    The lines are read from Transfermarkt's club pages on another machine
    (Transfermarkt throttles the API's IP) and sent here.
    """

    repository: PlayerRepository

    def execute(
        self, competition: str, season_label: str, rows: list[ScrapedSeasonRow]
    ) -> IngestionResult:
        # A move inside the league during the season: one line, both clubs.
        merged: dict[int, tuple[ScrapedSeasonRow, Statistics, list[str]]] = {}
        for row in rows:
            if row.transfermarkt_id in merged:
                first, total, teams = merged[row.transfermarkt_id]
                merged[row.transfermarkt_id] = (
                    first,
                    _added(total, row.statistics),
                    [*teams, row.team],
                )
            else:
                merged[row.transfermarkt_id] = (row, row.statistics, [row.team])

        known = self.repository.transfermarkt_index()
        season = Season(competition, season_label)
        for transfermarkt_id, (row, statistics, teams) in merged.items():
            player_id = known.get(transfermarkt_id)
            if player_id is None:
                player_id = TRANSFERMARKT_ID_OFFSET + transfermarkt_id
                self.repository.save_player(
                    Player(
                        player_id,
                        row.name,
                        row.position,
                        None,
                        detailed_position=row.detailed_position,
                    )
                )
                self.repository.set_transfermarkt_id(player_id, transfermarkt_id)
            self.repository.save_season_statistics(
                player_id, season, statistics, ", ".join(teams)
            )
        return IngestionResult(ingested=len(merged), skipped=[])
