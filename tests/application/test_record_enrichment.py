from datetime import date

import pytest

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.ports import MarketValueHistoryResult
from player_scouting.application.use_cases.record_enrichment import (
    RecordEnrichmentUseCase,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from tests.application.doubles import InMemoryPlayerRepository


def _repository():
    repository = InMemoryPlayerRepository()
    repository.save_player(Player(1, "Rodri", "Midfielder", None, birth_year=1996))
    return repository


def test_stores_what_was_found_and_marks_the_player_checked():
    repository = _repository()
    result = MarketValueHistoryResult(
        preferred_foot="right",
        points=[MarketValuePoint(date(2026, 6, 1), 55_000_000, "Manchester City")],
        photo_url="https://img.a.transfermarkt.technology/portrait/header/357565-1.jpg",
        date_of_birth=date(1996, 6, 22),
    )

    RecordEnrichmentUseCase(repository).execute(1, result)

    player = repository.get_player(1)
    assert player.date_of_birth == date(1996, 6, 22)
    assert player.photo_url.endswith("357565-1.jpg")
    assert repository.list_market_value_history(1)[0].amount_eur == 55_000_000
    assert repository.is_enrichment_checked(1)


def test_not_found_only_marks_the_player_checked():
    repository = _repository()

    RecordEnrichmentUseCase(repository).execute(1, None)

    assert repository.get_player(1).photo_url is None
    assert repository.is_enrichment_checked(1)


def test_unknown_player_raises():
    with pytest.raises(PlayerNotFoundError):
        RecordEnrichmentUseCase(_repository()).execute(99, None)
