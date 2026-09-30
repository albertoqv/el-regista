from __future__ import annotations

from datetime import datetime

from player_scouting.application.player_matching import ExternalPlayer
from player_scouting.application.ports import AdvancedSeasonRow, MatchRef
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
