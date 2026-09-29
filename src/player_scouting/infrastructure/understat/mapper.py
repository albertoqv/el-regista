from __future__ import annotations

from player_scouting.application.player_matching import ExternalPlayer
from player_scouting.application.ports import AdvancedSeasonRow
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
