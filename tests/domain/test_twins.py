from player_scouting.domain.twins import MINIMUM_SHARED_METRICS, style_similarity


def _profile(**percentiles: int) -> dict[str, int]:
    return percentiles


def test_identical_profiles_are_100_percent_alike():
    profile = _profile(goals=90, assists=40, shots=80, tackles_won=10, key_passes=60)

    result = style_similarity(profile, profile)

    assert result is not None
    assert result.percentage == 100


def test_similarity_is_100_minus_the_mean_percentile_gap():
    target = _profile(goals=90, assists=40, shots=80, tackles_won=10, key_passes=60)
    candidate = _profile(goals=80, assists=50, shots=80, tackles_won=30, key_passes=60)

    result = style_similarity(target, candidate)

    # Gaps 10, 10, 0, 20, 0 -> mean 8.
    assert result is not None
    assert result.percentage == 92


def test_only_metrics_both_players_have_are_compared():
    target = _profile(
        goals=90, assists=40, shots=80, tackles_won=10, key_passes=60, xg_chain=99
    )
    candidate = _profile(goals=90, assists=40, shots=80, tackles_won=10, key_passes=60)

    result = style_similarity(target, candidate)

    assert result is not None
    assert result.percentage == 100


def test_too_few_shared_metrics_cannot_be_compared():
    target = _profile(goals=90, assists=40)
    candidate = _profile(goals=90, assists=40)

    assert MINIMUM_SHARED_METRICS > 2
    assert style_similarity(target, candidate) is None


def test_shared_strengths_are_the_closest_metrics_where_the_target_stands_out():
    target = _profile(goals=95, assists=20, shots=90, tackles_won=10, key_passes=85)
    candidate = _profile(goals=93, assists=20, shots=70, tackles_won=60, key_passes=84)

    result = style_similarity(target, candidate)

    assert result is not None
    # assists and tackles are close or far but not strengths of the target.
    assert result.shared_strengths == ("key_passes", "goals", "shots")
    assert result.differences[0] == "tackles_won"


def test_a_basic_comparison_can_use_fewer_metrics_when_asked():
    target = _profile(goals=90, assists=40)
    candidate = _profile(goals=80, assists=40)

    result = style_similarity(target, candidate, minimum_shared=2)

    assert result is not None
    assert result.percentage == 95
