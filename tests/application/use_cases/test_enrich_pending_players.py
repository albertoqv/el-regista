from datetime import date

from player_scouting.application.ports import MarketValueHistoryResult
from player_scouting.application.use_cases.enrich_pending_players import (
    EnrichPendingPlayersUseCase,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from tests.application.doubles import FakeMarketValueProvider, InMemoryPlayerRepository

LA_LIGA_2026 = Season("La Liga", "2026")

YAMAL_PROFILE = MarketValueHistoryResult(
    preferred_foot="left",
    points=[MarketValuePoint(date(2026, 6, 1), 200_000_000, "FC Barcelona")],
    photo_url="https://img.a.transfermarkt.technology/portrait/header/937958.jpg",
    date_of_birth=date(2007, 7, 13),
)


def _repository() -> InMemoryPlayerRepository:
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Lamine Yamal", "Forward", None, birth_year=2007),
        LA_LIGA_2026,
        Statistics(7, 4),
    )
    repository.add(
        Player(2, "Bench Player", "Defender", None, birth_year=2001),
        LA_LIGA_2026,
        Statistics(0, 0),
    )
    return repository


def _use_case(provider, repository) -> EnrichPendingPlayersUseCase:
    return EnrichPendingPlayersUseCase(provider, repository, pause=lambda s: None)


def test_enriches_the_most_relevant_pending_players_first():
    repository = _repository()
    provider = FakeMarketValueProvider(results_by_name={"Lamine Yamal": YAMAL_PROFILE})

    result = _use_case(provider, repository).execute(limit=1)

    assert result.ingested == 1
    assert provider.requests == [("Lamine Yamal", 2007)]
    player = repository.get_player(1)
    assert player.photo_url == YAMAL_PROFILE.photo_url
    assert player.date_of_birth == date(2007, 7, 13)
    assert player.preferred_foot == "left"
    assert repository.list_market_value_history(1)[0].amount_eur == 200_000_000


def test_players_not_found_are_marked_so_they_are_not_retried():
    repository = _repository()
    provider = FakeMarketValueProvider(results_by_name={"Lamine Yamal": YAMAL_PROFILE})

    result = _use_case(provider, repository).execute(limit=10)

    assert result.ingested == 1
    assert [s.name for s in result.skipped] == ["Bench Player"]
    assert repository.is_enrichment_checked(2)
    assert _use_case(provider, repository).execute(limit=10).ingested == 0
    assert len(provider.requests) == 2


def test_stops_without_marking_anyone_when_the_source_blocks_us():
    repository = _repository()
    provider = FakeMarketValueProvider(
        results_by_name={"Lamine Yamal": YAMAL_PROFILE}, blocked_after=1
    )

    result = _use_case(provider, repository).execute(limit=10)

    assert result.ingested == 1
    assert repository.is_enrichment_checked(1)
    assert not repository.is_enrichment_checked(2)


def test_keeps_the_existing_exact_birth_date_when_transfermarkt_has_none():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Old Star", "Forward", date(1990, 5, 5)),
        LA_LIGA_2026,
        Statistics(1, 1),
    )
    provider = FakeMarketValueProvider(
        result=MarketValueHistoryResult(preferred_foot="right", points=[])
    )

    _use_case(provider, repository).execute(limit=1)

    assert repository.get_player(1).date_of_birth == date(1990, 5, 5)
