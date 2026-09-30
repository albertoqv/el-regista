from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace

from player_scouting.application.ingestion_result import IngestionResult, SkippedPlayer
from player_scouting.application.player_matching import name_tokens
from player_scouting.application.ports import (
    DatasetProfile,
    PlayerRepository,
    TransfermarktDatasetProvider,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season

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
        return partial[0] if len(partial) == 1 else None


@dataclass
class EnrichFromDatasetUseCase:
    """Photos, birth dates, height, role and market values for our players."""

    provider: TransfermarktDatasetProvider
    repository: PlayerRepository

    def execute(self) -> IngestionResult:
        known = self.repository.transfermarkt_index()
        index = _PlayerIndex(self.repository.list_players())
        matched = 0
        for profile in self.provider.profiles():
            player_id = known.get(profile.transfermarkt_id)
            player = (
                self.repository.get_player(player_id)
                if player_id is not None
                else index.find(profile)
            )
            if player is None:
                continue
            if player_id is None:
                self.repository.set_transfermarkt_id(
                    player.player_id, profile.transfermarkt_id
                )
            self._apply(player, profile)
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
        player_id = TRANSFERMARKT_ID_OFFSET + profile.transfermarkt_id
        self.repository.save_player(
            Player(
                player_id,
                profile.name,
                profile.position,
                profile.date_of_birth,
                photo_url=profile.photo_url,
                preferred_foot=profile.foot,
                birth_year=profile.date_of_birth.year
                if profile.date_of_birth
                else None,
                height_cm=profile.height_cm,
                detailed_position=profile.detailed_position,
            )
        )
        self.repository.set_transfermarkt_id(player_id, profile.transfermarkt_id)
        if profile.valuations:
            self.repository.save_market_value_history(
                player_id, sorted(profile.valuations, key=lambda p: p.as_of)
            )
        return player_id
