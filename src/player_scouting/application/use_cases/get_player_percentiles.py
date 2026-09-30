from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.ports import PlayerRepository
from player_scouting.domain.percentiles import MetricPercentile, percentile_profile
from player_scouting.domain.season import Season

# Peers need this share of the busiest player's minutes, and at least one match.
MINIMUM_MINUTES_SHARE = 0.3
MINIMUM_MINUTES_FLOOR = 90


@dataclass(frozen=True)
class PercentileReport:
    season: Season
    position: str
    peer_count: int
    minimum_minutes: int
    metrics: dict[str, MetricPercentile]


@dataclass
class GetPlayerPercentilesUseCase:
    repository: PlayerRepository

    def execute(self, player_id: int, season: Season) -> PercentileReport:
        entries = self.repository.list_season_entries(season)
        target = next(
            (entry for entry in entries if entry.player.player_id == player_id), None
        )
        if target is None:
            raise PlayerNotFoundError(
                f"No statistics for player {player_id} in {season}"
            )

        busiest = max(entry.statistics.minutes_played for entry in entries)
        minimum_minutes = max(
            MINIMUM_MINUTES_FLOOR, int(busiest * MINIMUM_MINUTES_SHARE)
        )
        peers = [
            entry.statistics
            for entry in entries
            if entry.player.position == target.player.position
            and (entry.statistics.minutes_played >= minimum_minutes or entry is target)
        ]
        return PercentileReport(
            season=season,
            position=target.player.position,
            peer_count=len(peers),
            minimum_minutes=minimum_minutes,
            metrics=percentile_profile(target.statistics, peers),
        )
