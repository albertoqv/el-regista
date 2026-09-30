from __future__ import annotations

from datetime import datetime

from player_scouting.application.player_matching import ExternalPlayer
from player_scouting.application.ports import (
    AdvancedSeasonRow,
    Fixture,
    MatchRef,
    TeamMatch,
)
from player_scouting.domain.shots import Shot
from player_scouting.domain.statistics import AdvancedStatistics


def _metric(raw: dict, key: str) -> float:
    return round(float(raw.get(key) or 0), 2)


def to_advanced_row(raw: dict, competition: str) -> AdvancedSeasonRow:
    return AdvancedSeasonRow(
        competition=competition,
        player=ExternalPlayer(
            external_id=int(raw["id"]),
            name=raw["player_name"],
            teams=tuple(team.strip() for team in raw["team_title"].split(",")),
            minutes=int(raw.get("time") or 0),
            goals=int(raw.get("goals") or 0),
        ),
        advanced=AdvancedStatistics(
            expected_goals=_metric(raw, "xG"),
            expected_assists=_metric(raw, "xA"),
            key_passes=int(raw.get("key_passes") or 0),
            xg_chain=_metric(raw, "xGChain"),
            xg_buildup=_metric(raw, "xGBuildup"),
        ),
    )


def to_match_ref(raw: dict, competition: str, season_label: str) -> MatchRef:
    return MatchRef(
        match_id=int(raw["id"]),
        competition=competition,
        season_label=season_label,
        played_on=datetime.strptime(raw["datetime"], "%Y-%m-%d %H:%M:%S").date(),
        home_team=raw["h"]["title"],
        away_team=raw["a"]["title"],
    )


def to_shot(raw: dict) -> Shot:
    return Shot(
        shot_id=int(raw["id"]),
        match_id=int(raw["match_id"]),
        understat_player_id=int(raw["player_id"]),
        player_name=raw["player"],
        minute=int(raw["minute"]),
        result=raw["result"],
        x=float(raw["X"]),
        y=float(raw["Y"]),
        xg=float(raw["xG"]),
        situation=raw["situation"],
        shot_type=raw["shotType"],
        home=raw["h_a"] == "h",
        assisted_by=raw.get("player_assisted") or None,
    )


def _kickoff(raw: dict) -> datetime:
    return datetime.strptime(raw["datetime"], "%Y-%m-%d %H:%M:%S")


def _optional_int(value: object) -> int | None:
    return None if value is None else int(str(value))


def _optional_float(value: object) -> float | None:
    return None if value is None else float(str(value))


def to_fixture(raw: dict, competition: str, season_label: str) -> Fixture:
    played = bool(raw.get("isResult"))
    return Fixture(
        match_id=int(raw["id"]),
        competition=competition,
        season_label=season_label,
        kickoff=_kickoff(raw),
        home_team=raw["h"]["title"],
        away_team=raw["a"]["title"],
        home_goals=_optional_int(raw["goals"]["h"]) if played else None,
        away_goals=_optional_int(raw["goals"]["a"]) if played else None,
        home_xg=_optional_float(raw["xG"]["h"]) if played else None,
        away_xg=_optional_float(raw["xG"]["a"]) if played else None,
    )


def _ratio(pair: dict) -> float | None:
    return pair["att"] / pair["def"] if pair.get("def") else None


def to_team_matches(
    league_data: dict, competition: str, season_label: str
) -> list[TeamMatch]:
    """Team history rows carry no match id: find it by kick-off, team and venue."""
    fixtures = {}
    for raw in league_data.get("dates", []):
        if raw.get("isResult"):
            fixtures[(raw["datetime"], raw["h"]["title"], "h")] = raw
            fixtures[(raw["datetime"], raw["a"]["title"], "a")] = raw
    matches = []
    for team in league_data.get("teams", {}).values():
        for row in team["history"]:
            fixture = fixtures.get((row["date"], team["title"], row["h_a"]))
            if fixture is None:
                continue
            home = row["h_a"] == "h"
            opponent = fixture["a" if home else "h"]["title"]
            matches.append(
                TeamMatch(
                    match_id=int(fixture["id"]),
                    competition=competition,
                    season_label=season_label,
                    played_on=_kickoff(fixture).date(),
                    team=team["title"],
                    opponent=opponent,
                    home=home,
                    goals_for=int(row["scored"]),
                    goals_against=int(row["missed"]),
                    xg_for=float(row["xG"]),
                    xg_against=float(row["xGA"]),
                    npxg_for=float(row["npxG"]),
                    npxg_against=float(row["npxGA"]),
                    ppda=_ratio(row["ppda"]),
                    ppda_allowed=_ratio(row["ppda_allowed"]),
                    deep=int(row["deep"]),
                    deep_allowed=int(row["deep_allowed"]),
                    xpts=float(row["xpts"]),
                    result=row["result"],
                )
            )
    return matches
