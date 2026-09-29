from player_scouting.infrastructure.statsbomb.competition_statistics_provider import (
    StatsBombCompetitionStatisticsProvider,
)

SCORER = {"id": 101, "name": "Scorer Player"}
ASSISTER = {"id": 102, "name": "Assister Player"}


class FakeStatsBombClient:
    def __init__(
        self, matches: list[dict], events_by_match: dict, lineups_by_match: dict
    ):
        self._matches = matches
        self._events_by_match = events_by_match
        self._lineups_by_match = lineups_by_match

    def get_matches(self, competition_id: int, season_id: int) -> list[dict]:
        return self._matches

    def get_events(self, match_id: int) -> list[dict]:
        return self._events_by_match[match_id]

    def get_lineups(self, match_id: int) -> list[dict]:
        return self._lineups_by_match[match_id]


def _shot_event(player: dict, outcome_name: str = "Goal") -> dict:
    return {
        "type": {"name": "Shot"},
        "player": player,
        "position": {"name": "Center Forward"},
        "shot": {"outcome": {"name": outcome_name}},
    }


def _lineup_for(player: dict, country_name: str) -> list[dict]:
    return [
        {
            "team_id": 1,
            "lineup": [
                {
                    "player_id": player["id"],
                    "player_name": player["name"],
                    "country": {"name": country_name},
                }
            ],
        }
    ]


def test_aggregates_goals_and_nationality_across_multiple_matches():
    client = FakeStatsBombClient(
        matches=[{"match_id": 1}, {"match_id": 2}],
        events_by_match={
            1: [_shot_event(SCORER)],
            2: [_shot_event(SCORER)],
        },
        lineups_by_match={
            1: _lineup_for(SCORER, "Argentina"),
            2: _lineup_for(SCORER, "Argentina"),
        },
    )
    provider = StatsBombCompetitionStatisticsProvider(client)

    stats = provider.get_statistics(competition_id=43, season_id=3)

    assert len(stats) == 1
    assert stats[0].player_id == 101
    assert stats[0].goals == 2
    assert stats[0].nationality == "Argentina"


def test_returns_no_nationality_when_lineup_does_not_include_the_player():
    client = FakeStatsBombClient(
        matches=[{"match_id": 1}],
        events_by_match={1: [_shot_event(SCORER)]},
        lineups_by_match={1: []},
    )
    provider = StatsBombCompetitionStatisticsProvider(client)

    stats = provider.get_statistics(competition_id=43, season_id=3)

    assert stats[0].nationality is None


def test_includes_players_who_did_not_score_or_assist():
    bench_defender = {"id": 201, "name": "Bench Defender"}
    lineups = [
        {
            "team_id": 1,
            "lineup": [
                {
                    "player_id": SCORER["id"],
                    "player_name": SCORER["name"],
                    "country": {"name": "Argentina"},
                },
                {
                    "player_id": bench_defender["id"],
                    "player_name": bench_defender["name"],
                    "country": {"name": "Brazil"},
                },
            ],
        }
    ]
    client = FakeStatsBombClient(
        matches=[{"match_id": 1}],
        events_by_match={1: [_shot_event(SCORER)]},
        lineups_by_match={1: lineups},
    )
    provider = StatsBombCompetitionStatisticsProvider(client)

    stats = provider.get_statistics(competition_id=43, season_id=3)

    stats_by_id = {s.player_id: s for s in stats}
    assert stats_by_id[201].goals == 0
    assert stats_by_id[201].assists == 0
    assert stats_by_id[201].nationality == "Brazil"
