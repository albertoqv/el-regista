from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.percentile_pools import (
    group_into_pools,
    pool_percentiles,
)
from player_scouting.application.ports import (
    PlayerRepository,
    SeasonRecord,
    ShotRepository,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.percentiles import MetricPercentile
from player_scouting.domain.roles import (
    HYBRID_DISTANCE,
    RoleMatch,
    role_distance,
    role_match,
    role_penalty,
)
from player_scouting.domain.season import Season
from player_scouting.domain.shots import shot_rates
from player_scouting.domain.twins import (
    BASIC_SHARED_METRICS,
    MINIMUM_SHARED_METRICS,
    style_similarity,
)

# A twin must have played enough for its per-90 profile to mean something.
TWIN_MINIMUM_MINUTES = 900
# Twins come from the most recent seasons: players you could sign today.
RECENT_SEASONS = 2
DEFAULT_LIMIT = 12


@dataclass(frozen=True)
class TwinFilters:
    max_value: int | None = None
    max_age: int | None = None
    competition: str | None = None
    limit: int = DEFAULT_LIMIT


@dataclass(frozen=True)
class TwinProfile:
    player: Player
    season: Season
    team: str | None
    market_value: MarketValuePoint | None
    percentiles: dict[str, MetricPercentile]


@dataclass(frozen=True)
class Twin(TwinProfile):
    similarity: int = 0
    role_match: RoleMatch | None = None
    shared_strengths: tuple[str, ...] = field(default=())
    differences: tuple[str, ...] = field(default=())


@dataclass(frozen=True)
class TwinReport:
    target: TwinProfile
    twins: list[Twin]
    # Only goals and assists to compare (leagues without a style profile).
    basic: bool = False


def _year(season: Season) -> int:
    return season.start_year or 0


def _age(player: Player, today: date) -> int | None:
    if player.date_of_birth is not None:
        born = player.date_of_birth
        return (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )
    if player.birth_year is not None:
        return today.year - player.birth_year
    return None


@dataclass
class FindTwinsUseCase:
    repository: PlayerRepository
    today: Callable[[], date] = field(default=date.today)
    # Optional: adds how and when they score (late goals, headers...) to the style.
    shots: ShotRepository | None = None

    def execute(
        self,
        player_id: int,
        season: Season | None = None,
        filters: TwinFilters | None = None,
    ) -> TwinReport:
        filters = filters or TwinFilters()
        player = self.repository.get_player(player_id)
        if player is None:
            raise PlayerNotFoundError(f"No player found with id {player_id}")

        own = self.repository.list_season_records(
            [season.label] if season else self._labels_of(player_id)
        )
        target = self._target_record(player_id, season, own)
        if target is None:
            raise PlayerNotFoundError(f"No statistics for player {player_id}")

        records = self._recent_records(target)
        candidates = self._candidate_records(target, records)
        keys = {self._key(r) for r in [target, *candidates]}
        pools = group_into_pools(
            ((r.season, r.player.position), self._key(r), r.statistics) for r in records
        )
        profiles = pool_percentiles(pools, keys, self._shot_rates(records))
        values = self.repository.latest_market_values()
        today = self.today()

        target_percentiles = profiles[self._key(target)]
        target_profile = {m: p.percentile for m, p in target_percentiles.items()}
        basic = len(target_profile) < MINIMUM_SHARED_METRICS
        role = target.player.detailed_position
        twins = []
        for record in candidates:
            if not self._passes(record, values, filters, today):
                continue
            # Without a style profile, the same role keeps it meaningful.
            if basic and role and record.player.detailed_position != role:
                continue
            percentiles = profiles[self._key(record)]
            similarity = style_similarity(
                target_profile,
                {m: p.percentile for m, p in percentiles.items()},
                BASIC_SHARED_METRICS if basic else MINIMUM_SHARED_METRICS,
            )
            if similarity is None:
                continue
            # Same numbers in another role is a weaker twin: the role weighs too.
            distance = role_distance(role, record.player.detailed_position)
            twins.append(
                Twin(
                    player=record.player,
                    season=record.season,
                    team=record.team,
                    market_value=values.get(record.player.player_id),
                    percentiles=percentiles,
                    similarity=max(0, similarity.percentage - role_penalty(distance)),
                    role_match=role_match(distance),
                    shared_strengths=similarity.shared_strengths,
                    differences=similarity.differences,
                )
            )
        twins.sort(key=lambda twin: (-twin.similarity, twin.player.name))
        return TwinReport(
            target=TwinProfile(
                player=target.player,
                season=target.season,
                team=target.team,
                market_value=values.get(player_id),
                percentiles=target_percentiles,
            ),
            twins=twins[: filters.limit],
            basic=basic,
        )

    def _shot_rates(
        self, records: list[SeasonRecord]
    ) -> dict[tuple[int, Season], dict[str, float]]:
        if self.shots is None:
            return {}
        totals = self.shots.list_shot_totals(sorted({r.season.label for r in records}))
        rates = {}
        for record in records:
            key = self._key(record)
            if key in totals:
                rates[key] = shot_rates(totals[key], record.statistics.minutes_played)
        return rates

    def _labels_of(self, player_id: int) -> list[str]:
        return [s.label for s in self.repository.list_seasons_for_player(player_id)]

    @staticmethod
    def _key(record: SeasonRecord) -> tuple[int, Season]:
        return (record.player.player_id, record.season)

    @staticmethod
    def _target_record(
        player_id: int, season: Season | None, records: list[SeasonRecord]
    ) -> SeasonRecord | None:
        own = [r for r in records if r.player.player_id == player_id]
        if season is not None:
            return next((r for r in own if r.season == season), None)
        own.sort(key=lambda r: (_year(r.season), r.statistics.minutes_played))
        regular = [
            r for r in own if r.statistics.minutes_played >= TWIN_MINIMUM_MINUTES
        ]
        # Latest season with real playing time; else simply the latest one.
        return (regular or own)[-1] if own else None

    def _recent_records(self, target: SeasonRecord) -> list[SeasonRecord]:
        today = self.today()
        current = today.year if today.month >= 7 else today.year - 1
        labels = {str(current - offset) for offset in range(RECENT_SEASONS)}
        labels.add(target.season.label)
        return self.repository.list_season_records(sorted(labels))

    @staticmethod
    def _candidate_records(
        target: SeasonRecord, records: list[SeasonRecord]
    ) -> list[SeasonRecord]:
        """Each other player's most recent season with enough minutes, same position."""
        best: dict[int, SeasonRecord] = {}
        for record in records:
            if (
                record.player.player_id == target.player.player_id
                or record.statistics.minutes_played < TWIN_MINIMUM_MINUTES
            ):
                continue
            if record.player.position != target.player.position:
                # Hybrids cross the line: a winger and a wide midfielder.
                distance = role_distance(
                    target.player.detailed_position, record.player.detailed_position
                )
                if distance is None or distance > HYBRID_DISTANCE:
                    continue
            current = best.get(record.player.player_id)
            if current is None or (
                _year(record.season),
                record.statistics.minutes_played,
            ) > (_year(current.season), current.statistics.minutes_played):
                best[record.player.player_id] = record
        return list(best.values())

    @staticmethod
    def _passes(
        record: SeasonRecord,
        values: dict[int, MarketValuePoint],
        filters: TwinFilters,
        today: date,
    ) -> bool:
        if filters.competition and record.season.competition != filters.competition:
            return False
        if filters.max_value is not None:
            value = values.get(record.player.player_id)
            if value is None or value.amount_eur > filters.max_value:
                return False
        if filters.max_age is not None:
            age = _age(record.player, today)
            if age is None or age > filters.max_age:
                return False
        return True
