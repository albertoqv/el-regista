from player_scouting.application.player_matching import (
    ExternalPlayer,
    MatchCandidate,
    match_players,
)


def _candidate(player_id, name, team="Real Madrid", minutes=600, goals=0):
    return MatchCandidate(
        player_id=player_id, name=name, team=team, minutes=minutes, goals=goals
    )


def _external(external_id, name, teams=("Real Madrid",), minutes=600, goals=0):
    return ExternalPlayer(
        external_id=external_id,
        name=name,
        teams=tuple(teams),
        minutes=minutes,
        goals=goals,
    )


def test_matches_identical_names_ignoring_accents_and_case():
    matches = match_players(
        [_external(1, "Vinícius Júnior")], [_candidate(10, "Vinicius Junior")]
    )

    assert matches == {1: 10}


def test_matches_when_one_name_contains_all_tokens_of_the_other():
    # Real case: Understat "Kylian Mbappe-Lottin" vs FBref "Kylian Mbappé".
    matches = match_players(
        [_external(1, "Kylian Mbappe-Lottin")],
        [_candidate(10, "Kylian Mbappé"), _candidate(11, "Jude Bellingham")],
    )

    assert matches == {1: 10}


def test_nickname_is_resolved_by_team_minutes_and_goals():
    # Real case: Understat "Pepelu" is listed with a different name in FBref.
    matches = match_players(
        [_external(1, "Pepelu", teams=("Valencia",), minutes=580, goals=1)],
        [
            _candidate(
                10, "José Luis García Vayá", team="Valencia", minutes=572, goals=1
            ),
            _candidate(11, "Hugo Duro", team="Valencia", minutes=580, goals=3),
        ],
    )

    assert matches == {1: 10}


def test_minutes_outside_the_tolerance_do_not_match():
    matches = match_players(
        [_external(1, "Pepelu", teams=("Valencia",), minutes=580, goals=1)],
        [
            _candidate(
                10, "José Luis García Vayá", team="Valencia", minutes=400, goals=1
            )
        ],
    )

    assert matches == {}


def test_ambiguous_token_matches_are_left_unmatched():
    matches = match_players(
        [_external(1, "Giménez", teams=("Atletico Madrid",), minutes=423, goals=0)],
        [
            _candidate(10, "José María Giménez", team="Atlético Madrid", minutes=1),
            _candidate(11, "Santiago Giménez", team="Milan", minutes=2),
        ],
    )

    assert matches == {}


def test_a_candidate_is_never_matched_twice():
    matches = match_players(
        [_external(1, "Rodri"), _external(2, "Rodri")],
        [_candidate(10, "Rodri")],
    )

    assert list(matches.values()) == [10]


def test_player_listed_with_two_teams_matches_either_team():
    # Understat lists mid-season transfers as "Atletico Madrid,Deportivo La Coruna".
    matches = match_players(
        [
            _external(
                1,
                "Nickname",
                teams=("Atletico Madrid", "Deportivo La Coruna"),
                minutes=423,
                goals=2,
            )
        ],
        [
            _candidate(
                10, "Real Full Name", team="Deportivo La Coruña", minutes=420, goals=2
            )
        ],
    )

    assert matches == {1: 10}
