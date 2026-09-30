from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

from player_scouting.application.ports import RosterEntry, ShotRepository

HotMetric = Literal["goals_assists", "goals", "threat", "form"]

MINIMUM_MINUTES = 180
# "Form" compares against his earlier pace, which needs enough earlier football.
MINIMUM_EARLIER_MINUTES = 270


@dataclass(frozen=True)
class HotPlayer:
    understat_player_id: int
    name: str
    team: str
    competition: str
    position: str
    matches: int
    minutes: int
    goals: int
    assists: int
    xg: float
    xa: float
    shots: int
    key_passes: int
    per90: float  # goals + assists per 90 in the window
    before_per90: float | None  # same, earlier this season


@dataclass(frozen=True)
class HotBoard:
    window_start: date
    window_end: date
    metric: HotMetric
    players: list[HotPlayer]


def _per90(entries: list[RosterEntry]) -> tuple[float, int]:
    minutes = sum(e.minutes for e in entries)
    involvement = sum(e.goals + e.assists for e in entries)
    return (involvement * 90 / minutes if minutes else 0.0), minutes


def _sort_key(metric: HotMetric) -> Callable[[HotPlayer], tuple[float, float]]:
    def key(player: HotPlayer) -> tuple[float, float]:
        threat = player.xg + player.xa
        if metric == "goals":
            return (player.goals, threat)
        if metric == "threat":
            return (threat, player.goals + player.assists)
        if metric == "form":
            return (player.per90 - (player.before_per90 or 0.0), threat)
        return (player.goals + player.assists, threat)

    return key


@dataclass
class HotPlayersUseCase:
    """Who is on fire: the last few weeks from Understat's match lineups."""

    shots: ShotRepository
    competitions: list[str]
    today: Callable[[], date] = field(default=date.today)

    def execute(
        self,
        season_label: str,
        days: int = 30,
        metric: HotMetric = "goals_assists",
        limit: int = 20,
        competition: str | None = None,
    ) -> HotBoard:
        end = self.today()
        start = end - timedelta(days=days)
        players: list[HotPlayer] = []
        for league in self.competitions:
            if competition and league != competition:
                continue
            by_player: dict[int, list[RosterEntry]] = defaultdict(list)
            for entry in self.shots.list_rosters(league, [season_label]):
                if entry.minutes > 0 and entry.played_on <= end:
                    by_player[entry.understat_player_id].append(entry)
            for entries in by_player.values():
                player = self._player(entries, start)
                if player is not None:
                    players.append(player)
        if metric == "form":
            players = [p for p in players if p.before_per90 is not None]
        players.sort(key=_sort_key(metric), reverse=True)
        return HotBoard(start, end, metric, players[:limit])

    @staticmethod
    def _player(entries: list[RosterEntry], start: date) -> HotPlayer | None:
        recent = [e for e in entries if e.played_on >= start]
        earlier = [e for e in entries if e.played_on < start]
        per90, minutes = _per90(recent)
        if minutes < MINIMUM_MINUTES:
            return None
        before, before_minutes = _per90(earlier)
        latest = max(recent, key=lambda e: e.played_on)
        return HotPlayer(
            understat_player_id=latest.understat_player_id,
            name=latest.player_name,
            team=latest.team,
            competition=latest.competition,
            position=latest.position,
            matches=len(recent),
            minutes=minutes,
            goals=sum(e.goals for e in recent),
            assists=sum(e.assists for e in recent),
            xg=sum(e.xg for e in recent),
            xa=sum(e.xa for e in recent),
            shots=sum(e.shots for e in recent),
            key_passes=sum(e.key_passes for e in recent),
            per90=per90,
            before_per90=(
                before if before_minutes >= MINIMUM_EARLIER_MINUTES else None
            ),
        )
