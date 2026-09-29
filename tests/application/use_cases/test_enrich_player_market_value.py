from datetime import date

from player_scouting.application.ports import MarketValueHistoryResult
from player_scouting.application.use_cases.enrich_player_market_value import (
    EnrichPlayerMarketValueUseCase,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from tests.application.doubles import FakeMarketValueProvider, InMemoryPlayerRepository

BELLINGHAM = Player(581678, "Jude Bellingham", "Midfielder", date(2003, 6, 29))


def test_enriches_an_existing_player_with_foot_and_market_value_history():
    provider = FakeMarketValueProvider(
        MarketValueHistoryResult(
            preferred_foot="right",
            points=[
                MarketValuePoint(date(2019, 10, 17), 2_500_000, "Birmingham City"),
                MarketValuePoint(date(2026, 1, 1), 160_000_000, "Real Madrid"),
            ],
        )
    )
    repository = InMemoryPlayerRepository()
    repository.save_player(BELLINGHAM)
    use_case = EnrichPlayerMarketValueUseCase(provider, repository)

    result = use_case.execute(BELLINGHAM.player_id, "Jude Bellingham")

    assert result.ingested == 1
    assert result.skipped == []
    player = repository.get_player(BELLINGHAM.player_id)
    assert player.preferred_foot == "right"
    history = repository.list_market_value_history(BELLINGHAM.player_id)
    assert len(history) == 2
    assert history[-1].amount_eur == 160_000_000


def test_reports_a_skipped_player_when_transfermarkt_finds_nothing():
    provider = FakeMarketValueProvider(None)
    repository = InMemoryPlayerRepository()
    repository.save_player(BELLINGHAM)
    use_case = EnrichPlayerMarketValueUseCase(provider, repository)

    result = use_case.execute(BELLINGHAM.player_id, "Jude Bellingham")

    assert result.ingested == 0
    assert len(result.skipped) == 1
    assert result.skipped[0].name == "Jude Bellingham"
    assert repository.get_player(BELLINGHAM.player_id).preferred_foot is None
