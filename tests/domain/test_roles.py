from player_scouting.domain.roles import role_distance, role_match, role_penalty


def test_the_same_role_is_distance_zero():
    assert role_distance("Right Winger", "Right Winger") == 0


def test_mirror_and_neighbouring_roles_are_close():
    assert role_distance("Right Winger", "Left Winger") == 1
    assert role_distance("Central Midfield", "Attacking Midfield") == 1
    assert role_distance("Right-Back", "Right Midfield") == 1


def test_far_roles_are_far():
    assert role_distance("Centre-Back", "Centre-Forward") >= 3


def test_an_unknown_role_says_nothing():
    assert role_distance(None, "Right Winger") is None
    assert role_distance("Libero", "Right Winger") is None


def test_the_penalty_grows_with_distance_and_is_neutral_when_unknown():
    assert role_penalty(0) == 0
    assert 0 < role_penalty(1) < role_penalty(2) < role_penalty(3)
    assert role_penalty(None) == 0


def test_role_match_labels():
    assert role_match(0) == "same"
    assert role_match(1) == "similar"
    assert role_match(3) == "different"
    assert role_match(None) is None
