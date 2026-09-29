from datetime import date

import pytest

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.use_cases.compare_players import ComparePlayersUseCase
from player_scouting.domain.entities import Player
from player_scouting.domain.similarity_calculator import SimilarityCalculator
from player_scouting.domain.statistics import Statistics
from player_scouting.domain.value_objects import SimilarityScore
from tests.application.doubles import InMemoryPlayerRepository


def test_compares_two_existing_players_by_their_statistics():
    repository = InMemoryPlayerRepository()
    player1 = Player(1, "Player One", "Forward", date(1995, 1, 1))
    player2 = Player(2, "Player Two", "Forward", date(1996, 1, 1))
    repository.add(player1, Statistics(10, 15))
    repository.add(player2, Statistics(15, 10))
    use_case = ComparePlayersUseCase(repository, SimilarityCalculator())

    comparison = use_case.execute(1, 2)

    assert comparison.player1 == player1
    assert comparison.player2 == player2
    assert comparison.similarity_score == SimilarityScore(67)


def test_raises_player_not_found_when_first_player_is_missing():
    repository = InMemoryPlayerRepository()
    repository.add(Player(2, "Player Two", "Forward", date(1996, 1, 1)), Statistics(15, 10))
    use_case = ComparePlayersUseCase(repository, SimilarityCalculator())

    with pytest.raises(PlayerNotFoundError):
        use_case.execute(1, 2)


def test_raises_player_not_found_when_second_player_is_missing():
    repository = InMemoryPlayerRepository()
    repository.add(Player(1, "Player One", "Forward", date(1995, 1, 1)), Statistics(10, 15))
    use_case = ComparePlayersUseCase(repository, SimilarityCalculator())

    with pytest.raises(PlayerNotFoundError):
        use_case.execute(1, 2)
