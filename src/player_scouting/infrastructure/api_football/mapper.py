from __future__ import annotations

from datetime import date

from player_scouting.application.ports import PlayerSeasonResult
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics


def to_player_season_result(
    player_info: dict, stats_block: dict, season_year: int
) -> PlayerSeasonResult:
    games = stats_block.get("games") or {}
    shots = stats_block.get("shots") or {}
    goals = stats_block.get("goals") or {}
    passes = stats_block.get("passes") or {}
    tackles = stats_block.get("tackles") or {}
    dribbles = stats_block.get("dribbles") or {}
    fouls = stats_block.get("fouls") or {}
    cards = stats_block.get("cards") or {}
    league = stats_block.get("league") or {}

    passes_attempted = passes.get("total") or 0
    accuracy = passes.get("accuracy") or 0
    passes_completed = round(passes_attempted * accuracy / 100)

    statistics = Statistics(
        goals=goals.get("total") or 0,
        assists=goals.get("assists") or 0,
        shots=shots.get("total") or 0,
        shots_on_target=shots.get("on") or 0,
        passes_completed=passes_completed,
        passes_attempted=passes_attempted,
        key_passes=passes.get("key") or 0,
        dribbles_completed=dribbles.get("success") or 0,
        dribbles_attempted=dribbles.get("attempts") or 0,
        tackles_won=tackles.get("total") or 0,
        interceptions=tackles.get("interceptions") or 0,
        fouls_committed=fouls.get("committed") or 0,
        fouls_won=fouls.get("drawn") or 0,
        yellow_cards=cards.get("yellow") or 0,
        red_cards=(cards.get("red") or 0) + (cards.get("yellowred") or 0),
    )

    season = Season(
        league.get("name") or "Unknown",
        str(league.get("season") or season_year),
    )

    return PlayerSeasonResult(
        player_id=player_info["id"],
        name=player_info["name"],
        position=games.get("position"),
        date_of_birth=date.fromisoformat(player_info["birth"]["date"]),
        season=season,
        statistics=statistics,
        photo_url=player_info.get("photo"),
    )
