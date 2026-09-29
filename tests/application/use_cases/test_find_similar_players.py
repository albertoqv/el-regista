from datetime import date

import pytest

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.use_cases.find_similar_players import (
    FindSimilarPlayersUseCase,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.similarity_calculator import SimilarityCalculator
from player_scouting.domain.statistics import Statistics
from tests.application.doubles import InMemoryPlayerRepository

LA_LIGA_2023 = Season("La Liga", "2023")
BUNDESLIGA_2022 = Season("Bundesliga", "2022")
PREMIER_LEAGUE_2019 = Season("Premier League", "2019")


def _repository_with_target_and_candidates() -> InMemoryPlayerRepository:
    repository = InMemoryPlayerRepository()
    target = Player(1, "Target", "Forward", date(1995, 1, 1))
    close_match = Player(2, "Close Match", "Forward", date(1996, 1, 1))
    far_match = Player(3, "Far Match", "Forward", date(1997, 1, 1))
    repository.add(target, LA_LIGA_2023, Statistics(10, 10))
    repository.add(close_match, BUNDESLIGA_2022, Statistics(10, 9))
    repository.add(far_match, PREMIER_LEAGUE_2019, Statistics(1, 1))
    return repository


def test_orders_candidates_by_similarity_descending_and_excludes_target():
    repository = _repository_with_target_and_candidates()
    use_case = FindSimilarPlayersUseCase(repository, SimilarityCalculator())

    results = use_case.execute(1)

    assert [match.comparison.player2.player_id for match in results] == [2, 3]
    first_score = results[0].comparison.similarity_score.percentage
    second_score = results[1].comparison.similarity_score.percentage
    assert first_score >= second_score


def test_reports_which_season_each_match_came_from():
    repository = _repository_with_target_and_candidates()
    use_case = FindSimilarPlayersUseCase(repository, SimilarityCalculator())

    results = use_case.execute(1)

    assert results[0].candidate_season == BUNDESLIGA_2022


def test_limits_results_to_top_n():
    repository = _repository_with_target_and_candidates()
    use_case = FindSimilarPlayersUseCase(repository, SimilarityCalculator())

    results = use_case.execute(1, top_n=1)

    assert len(results) == 1
    assert results[0].comparison.player2.player_id == 2


def test_uses_a_specific_season_as_the_reference_when_given():
    repository = _repository_with_target_and_candidates()
    repository.add(
        Player(1, "Target", "Forward", date(1995, 1, 1)),
        PREMIER_LEAGUE_2019,
        Statistics(1, 1),
    )
    use_case = FindSimilarPlayersUseCase(repository, SimilarityCalculator())

    results = use_case.execute(1, season=PREMIER_LEAGUE_2019)

    assert results[0].comparison.player2.player_id == 3


def test_returns_empty_list_when_no_other_season_records_exist():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Target", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 10),
    )
    use_case = FindSimilarPlayersUseCase(repository, SimilarityCalculator())

    results = use_case.execute(1)

    assert results == []


def test_raises_player_not_found_when_target_is_missing():
    repository = InMemoryPlayerRepository()
    use_case = FindSimilarPlayersUseCase(repository, SimilarityCalculator())

    with pytest.raises(PlayerNotFoundError):
        use_case.execute(1)
