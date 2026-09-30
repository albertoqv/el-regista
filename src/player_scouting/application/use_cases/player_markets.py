from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from player_scouting.application.ports import (
    Fixture,
    RosterEntry,
    ShotProvider,
    ShotRepository,
    TeamRepository,
)
from player_scouting.application.use_cases.team_analytics import (
    _labels_up_to,
    _record,
)
from player_scouting.domain.player_props import (
    Appearance,
    PlayerProps,
    expected_minutes,
    main_position,
    minutes_when_playing,
    player_props,
    playing_chance,
)
from player_scouting.domain.prediction import predict, team_ratings

RECENT_TEAM_MATCHES = 6
MINIMUM_EXPECTED_MINUTES = 5
PAUSE_BETWEEN_MATCHES_SECONDS = 1.0


@dataclass(frozen=True)
class RosterIngestionSummary:
    matches: int
    players: int
    remaining: int


@dataclass
class IngestRostersUseCase:
    provider: ShotProvider
    repository: ShotRepository
    pause: Callable[[float], None] = field(default=time.sleep)

    def execute(self, start_year: int, limit: int) -> RosterIngestionSummary:
        pending = self.repository.matches_without_rosters(str(start_year), limit + 1)
        batch = pending[:limit]
        players = 0
        for index, match in enumerate(batch):
            if index:
                self.pause(PAUSE_BETWEEN_MATCHES_SECONDS)
            entries = self.provider.get_match_rosters(match)
            self.repository.save_rosters(match.match_id, entries)
            players += len(entries)
        remaining = len(
            self.repository.matches_without_rosters(str(start_year), 10_000)
        )
        return RosterIngestionSummary(len(batch), players, remaining)


@dataclass(frozen=True)
class PlayerMarketLine:
    """Markets are priced *if he plays* (bookmakers void bets on non-starters);
    `plays` is the separate chance that he features at all."""

    understat_player_id: int
    name: str
    position: str
    plays: float
    props: PlayerProps


@dataclass(frozen=True)
class PlayerMarkets:
    fixture: Fixture
    home: list[PlayerMarketLine]
    away: list[PlayerMarketLine]


def _appearance(entry: RosterEntry) -> Appearance:
    return Appearance(
        entry.minutes, entry.xg, entry.xa, entry.shots, entry.yellow, entry.position
    )


def _team_lines(
    team: str,
    rosters: list[RosterEntry],
    before: date,
    expected_team_goals: float | None,
) -> list[PlayerMarketLine]:
    """Every player seen in the team's recent matches, priced for the next one."""
    own = [r for r in rosters if r.team == team and r.played_on < before]
    match_day = {r.match_id: r.played_on for r in own}
    recent_ids = sorted(match_day, key=lambda m: match_day[m], reverse=True)[
        :RECENT_TEAM_MATCHES
    ]
    if not recent_ids:
        return []
    minutes_by_match: dict[int, dict[int, int]] = defaultdict(dict)
    team_xg: dict[int, float] = defaultdict(float)
    for entry in own:
        if entry.match_id in recent_ids:
            minutes_by_match[entry.match_id][entry.understat_player_id] = entry.minutes
            team_xg[entry.match_id] += entry.xg
    usual_xg = sum(team_xg.values()) / len(recent_ids)
    factor = (
        expected_team_goals / usual_xg
        if expected_team_goals is not None and usual_xg > 0
        else 1.0
    )
    history: dict[int, list[RosterEntry]] = defaultdict(list)
    for entry in own:
        history[entry.understat_player_id].append(entry)
    lines = []
    for player_id, entries in history.items():
        recent = [minutes_by_match[m].get(player_id, 0) for m in recent_ids]
        if expected_minutes(recent) < MINIMUM_EXPECTED_MINUTES:
            continue
        minutes = minutes_when_playing(recent)
        latest = max(entries, key=lambda e: e.played_on)
        lines.append(
            PlayerMarketLine(
                understat_player_id=player_id,
                name=latest.player_name,
                position=main_position([_appearance(e) for e in entries]),
                plays=playing_chance(recent),
                props=player_props(
                    [_appearance(e) for e in entries],
                    minutes=minutes,
                    team_factor=factor,
                    card_factor=1.0,
                ),
            )
        )
    return sorted(lines, key=lambda line: -line.props.goal)


@dataclass
class PlayerMarketsUseCase:
    teams: TeamRepository
    shots: ShotRepository
    today: Callable[[], date] = field(default=date.today)

    def execute(self, match_id: int) -> PlayerMarkets | None:
        fixture = next(
            (f for f in self.teams.list_fixtures() if f.match_id == match_id), None
        )
        if fixture is None:
            return None
        labels = _labels_up_to(fixture.season_label)
        history = self.teams.list_team_matches(labels, fixture.competition)
        prediction = predict(
            team_ratings([_record(m) for m in history], self.today()),
            fixture.home_team,
            fixture.away_team,
        )
        rosters = self.shots.list_rosters(fixture.competition, labels)
        kickoff = fixture.kickoff.date()
        return PlayerMarkets(
            fixture=fixture,
            home=_team_lines(
                fixture.home_team, rosters, kickoff, prediction.expected_home
            ),
            away=_team_lines(
                fixture.away_team, rosters, kickoff, prediction.expected_away
            ),
        )


@dataclass(frozen=True)
class PlayerMarketsBacktest:
    predictions: int
    brier: float
    baseline_brier: float
    calibration: list[tuple[float, float, int]]


@dataclass
class PlayerMarketsBacktestUseCase:
    """Anytime scorer, walk-forward: each match priced only with earlier rosters.

    The team's expected goals are left at its usual level, so this tests the
    player part of the model on its own. Baseline: the league-wide share of
    players who score in a match, for everyone.
    """

    shots: ShotRepository
    minimum_matches: int = 5

    def execute(self, competition: str, season_label: str) -> PlayerMarketsBacktest:
        rosters = self.shots.list_rosters(competition, _labels_up_to(season_label))
        matches = sorted(
            {
                (r.played_on, r.match_id)
                for r in rosters
                if r.season_label == season_label
            }
        )
        scored: list[tuple[float, float, int]] = []
        for played_on, match_id in matches:
            earlier = [r for r in rosters if r.played_on < played_on]
            if len({r.match_id for r in earlier}) < self.minimum_matches:
                continue
            baseline = sum(r.goals > 0 for r in earlier) / len(earlier)
            actual = {
                (r.team, r.understat_player_id): r.goals > 0
                for r in rosters
                if r.match_id == match_id and r.minutes > 0
            }
            for team in {team for team, _ in actual}:
                for line in _team_lines(team, earlier, played_on, None):
                    key = (team, line.understat_player_id)
                    if key not in actual:
                        continue  # did not play: the minutes model already priced that
                    scored.append((line.props.goal, baseline, int(actual[key])))
        if not scored:
            return PlayerMarketsBacktest(0, 0.0, 0.0, [])
        buckets: dict[int, list[tuple[float, int]]] = defaultdict(list)
        for probability, _, outcome in scored:
            buckets[min(int(probability * 10), 9)].append((probability, outcome))
        count = len(scored)
        return PlayerMarketsBacktest(
            predictions=count,
            brier=sum((p - o) ** 2 for p, _, o in scored) / count,
            baseline_brier=sum((b - o) ** 2 for _, b, o in scored) / count,
            calibration=[
                (
                    sum(p for p, _ in items) / len(items),
                    sum(o for _, o in items) / len(items),
                    len(items),
                )
                for _, items in sorted(buckets.items())
            ],
        )
