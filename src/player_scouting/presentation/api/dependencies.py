from __future__ import annotations

import time
from collections.abc import Callable
from typing import Annotated

import httpx
from fastapi import Depends
from sqlalchemy.orm import Session

from player_scouting.application.league_ingestion_job import (
    LeagueIngestionJobRepository,
)
from player_scouting.application.use_cases.compare_players import ComparePlayersUseCase
from player_scouting.application.use_cases.enqueue_league_ingestion import (
    EnqueueLeagueIngestionUseCase,
)
from player_scouting.application.use_cases.enrich_pending_players import (
    EnrichPendingPlayersUseCase,
)
from player_scouting.application.use_cases.enrich_player_market_value import (
    EnrichPlayerMarketValueUseCase,
)
from player_scouting.application.use_cases.find_similar_players import (
    FindSimilarPlayersUseCase,
)
from player_scouting.application.use_cases.find_twins import FindTwinsUseCase
from player_scouting.application.use_cases.get_player_percentiles import (
    GetPlayerPercentilesUseCase,
)
from player_scouting.application.use_cases.ingest_advanced_season import (
    IngestAdvancedSeasonUseCase,
)
from player_scouting.application.use_cases.ingest_competition import (
    IngestCompetitionUseCase,
)
from player_scouting.application.use_cases.ingest_player_season import (
    IngestPlayerSeasonUseCase,
)
from player_scouting.application.use_cases.ingest_season_dataset import (
    IngestSeasonDatasetUseCase,
)
from player_scouting.application.use_cases.ingest_season_shots import (
    IngestSeasonShotsUseCase,
)
from player_scouting.application.use_cases.merge_duplicate_players import (
    MergeDuplicatePlayersUseCase,
)
from player_scouting.application.use_cases.process_league_ingestion_batch import (
    ProcessLeagueIngestionBatchUseCase,
)
from player_scouting.application.use_cases.record_enrichment import (
    RecordEnrichmentUseCase,
)
from player_scouting.domain.similarity_calculator import SimilarityCalculator
from player_scouting.infrastructure.api_football.league_provider import (
    ApiFootballLeaguePlayersProvider,
)
from player_scouting.infrastructure.api_football.league_search_provider import (
    ApiFootballLeagueSearchProvider,
)
from player_scouting.infrastructure.api_football.provider import (
    ApiFootballPlayerSeasonProvider,
)
from player_scouting.infrastructure.api_football.settings import (
    get_api_football_settings,
)
from player_scouting.infrastructure.birth_dates.wikidata_provider import (
    WikidataBirthDateProvider,
)
from player_scouting.infrastructure.fbref_kaggle.client import FbrefKaggleClient
from player_scouting.infrastructure.fbref_kaggle.provider import (
    FbrefKaggleSeasonProvider,
)
from player_scouting.infrastructure.persistence.database import get_session
from player_scouting.infrastructure.persistence.sqlalchemy_league_ingestion_job_repository import (  # noqa: E501
    SqlAlchemyLeagueIngestionJobRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_player_repository import (
    SqlAlchemyPlayerRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_shot_repository import (
    SqlAlchemyShotRepository,
)
from player_scouting.infrastructure.statsbomb.client import StatsBombClient
from player_scouting.infrastructure.statsbomb.competition_statistics_provider import (
    StatsBombCompetitionStatisticsProvider,
)
from player_scouting.infrastructure.transfermarkt.client import TransfermarktClient
from player_scouting.infrastructure.transfermarkt.provider import (
    TransfermarktMarketValueProvider,
)
from player_scouting.infrastructure.understat.client import UnderstatClient
from player_scouting.infrastructure.understat.provider import (
    UnderstatSeasonProvider,
)
from player_scouting.infrastructure.understat.shot_provider import (
    UnderstatShotProvider,
)

SessionDep = Annotated[Session, Depends(get_session)]


def get_player_repository(session: SessionDep) -> SqlAlchemyPlayerRepository:
    return SqlAlchemyPlayerRepository(session)


def get_similarity_calculator() -> SimilarityCalculator:
    return SimilarityCalculator()


PlayerRepositoryDep = Annotated[
    SqlAlchemyPlayerRepository, Depends(get_player_repository)
]
SimilarityCalculatorDep = Annotated[
    SimilarityCalculator, Depends(get_similarity_calculator)
]


def get_compare_players_use_case(
    repository: PlayerRepositoryDep,
    calculator: SimilarityCalculatorDep,
) -> ComparePlayersUseCase:
    return ComparePlayersUseCase(repository, calculator)


def get_find_similar_players_use_case(
    repository: PlayerRepositoryDep,
    calculator: SimilarityCalculatorDep,
) -> FindSimilarPlayersUseCase:
    return FindSimilarPlayersUseCase(repository, calculator)


def get_statsbomb_client() -> StatsBombClient:
    return StatsBombClient()


StatsBombClientDep = Annotated[StatsBombClient, Depends(get_statsbomb_client)]


def get_statistics_provider(
    client: StatsBombClientDep,
) -> StatsBombCompetitionStatisticsProvider:
    return StatsBombCompetitionStatisticsProvider(client)


def get_birth_date_provider() -> WikidataBirthDateProvider:
    return WikidataBirthDateProvider()


StatisticsProviderDep = Annotated[
    StatsBombCompetitionStatisticsProvider, Depends(get_statistics_provider)
]
BirthDateProviderDep = Annotated[
    WikidataBirthDateProvider, Depends(get_birth_date_provider)
]


def get_ingest_competition_use_case(
    statistics_provider: StatisticsProviderDep,
    birth_date_provider: BirthDateProviderDep,
    repository: PlayerRepositoryDep,
) -> IngestCompetitionUseCase:
    return IngestCompetitionUseCase(
        statistics_provider, birth_date_provider, repository
    )


def get_api_football_http_client() -> httpx.Client:
    return httpx.Client()


ApiFootballHttpClientDep = Annotated[
    httpx.Client, Depends(get_api_football_http_client)
]


def get_player_season_statistics_provider(
    http_client: ApiFootballHttpClientDep,
) -> ApiFootballPlayerSeasonProvider:
    return ApiFootballPlayerSeasonProvider(
        http_client=http_client,
        api_key=get_api_football_settings().api_football_key,
    )


PlayerSeasonStatisticsProviderDep = Annotated[
    ApiFootballPlayerSeasonProvider, Depends(get_player_season_statistics_provider)
]


def get_ingest_player_season_use_case(
    provider: PlayerSeasonStatisticsProviderDep,
    repository: PlayerRepositoryDep,
) -> IngestPlayerSeasonUseCase:
    return IngestPlayerSeasonUseCase(provider, repository)


ComparePlayersUseCaseDep = Annotated[
    ComparePlayersUseCase, Depends(get_compare_players_use_case)
]
FindSimilarPlayersUseCaseDep = Annotated[
    FindSimilarPlayersUseCase, Depends(get_find_similar_players_use_case)
]
IngestCompetitionUseCaseDep = Annotated[
    IngestCompetitionUseCase, Depends(get_ingest_competition_use_case)
]
IngestPlayerSeasonUseCaseDep = Annotated[
    IngestPlayerSeasonUseCase, Depends(get_ingest_player_season_use_case)
]


def get_transfermarkt_http_client() -> httpx.Client:
    return httpx.Client()


TransfermarktHttpClientDep = Annotated[
    httpx.Client, Depends(get_transfermarkt_http_client)
]


def get_transfermarkt_client(
    http_client: TransfermarktHttpClientDep,
) -> TransfermarktClient:
    return TransfermarktClient(http_client=http_client)


TransfermarktClientDep = Annotated[
    TransfermarktClient, Depends(get_transfermarkt_client)
]


def get_market_value_provider(
    client: TransfermarktClientDep,
) -> TransfermarktMarketValueProvider:
    return TransfermarktMarketValueProvider(client)


MarketValueProviderDep = Annotated[
    TransfermarktMarketValueProvider, Depends(get_market_value_provider)
]


def get_enrich_player_market_value_use_case(
    provider: MarketValueProviderDep,
    repository: PlayerRepositoryDep,
) -> EnrichPlayerMarketValueUseCase:
    return EnrichPlayerMarketValueUseCase(provider, repository)


EnrichPlayerMarketValueUseCaseDep = Annotated[
    EnrichPlayerMarketValueUseCase, Depends(get_enrich_player_market_value_use_case)
]


def get_league_ingestion_job_repository(
    session: SessionDep,
) -> SqlAlchemyLeagueIngestionJobRepository:
    return SqlAlchemyLeagueIngestionJobRepository(session)


LeagueIngestionJobRepositoryDep = Annotated[
    LeagueIngestionJobRepository, Depends(get_league_ingestion_job_repository)
]


def get_league_search_provider(
    http_client: ApiFootballHttpClientDep,
) -> ApiFootballLeagueSearchProvider:
    return ApiFootballLeagueSearchProvider(
        http_client=http_client,
        api_key=get_api_football_settings().api_football_key,
    )


LeagueSearchProviderDep = Annotated[
    ApiFootballLeagueSearchProvider, Depends(get_league_search_provider)
]


def get_league_players_provider(
    http_client: ApiFootballHttpClientDep,
) -> ApiFootballLeaguePlayersProvider:
    return ApiFootballLeaguePlayersProvider(
        http_client=http_client,
        api_key=get_api_football_settings().api_football_key,
    )


LeaguePlayersProviderDep = Annotated[
    ApiFootballLeaguePlayersProvider, Depends(get_league_players_provider)
]


def get_enqueue_league_ingestion_use_case(
    repository: LeagueIngestionJobRepositoryDep,
) -> EnqueueLeagueIngestionUseCase:
    return EnqueueLeagueIngestionUseCase(repository)


EnqueueLeagueIngestionUseCaseDep = Annotated[
    EnqueueLeagueIngestionUseCase, Depends(get_enqueue_league_ingestion_use_case)
]


def get_process_league_ingestion_batch_use_case(
    provider: LeaguePlayersProviderDep,
    player_repository: PlayerRepositoryDep,
    job_repository: LeagueIngestionJobRepositoryDep,
) -> ProcessLeagueIngestionBatchUseCase:
    return ProcessLeagueIngestionBatchUseCase(
        provider, player_repository, job_repository
    )


ProcessLeagueIngestionBatchUseCaseDep = Annotated[
    ProcessLeagueIngestionBatchUseCase,
    Depends(get_process_league_ingestion_batch_use_case),
]


def get_season_dataset_provider() -> FbrefKaggleSeasonProvider:
    return FbrefKaggleSeasonProvider(FbrefKaggleClient(httpx.Client()))


SeasonDatasetProviderDep = Annotated[
    FbrefKaggleSeasonProvider, Depends(get_season_dataset_provider)
]


def get_ingest_season_dataset_use_case(
    provider: SeasonDatasetProviderDep,
    repository: PlayerRepositoryDep,
) -> IngestSeasonDatasetUseCase:
    return IngestSeasonDatasetUseCase(provider, repository)


IngestSeasonDatasetUseCaseDep = Annotated[
    IngestSeasonDatasetUseCase, Depends(get_ingest_season_dataset_use_case)
]


def get_advanced_season_provider() -> UnderstatSeasonProvider:
    return UnderstatSeasonProvider(UnderstatClient(httpx.Client()))


AdvancedSeasonProviderDep = Annotated[
    UnderstatSeasonProvider, Depends(get_advanced_season_provider)
]


def get_ingest_advanced_season_use_case(
    provider: AdvancedSeasonProviderDep,
    repository: PlayerRepositoryDep,
) -> IngestAdvancedSeasonUseCase:
    return IngestAdvancedSeasonUseCase(provider, repository)


IngestAdvancedSeasonUseCaseDep = Annotated[
    IngestAdvancedSeasonUseCase, Depends(get_ingest_advanced_season_use_case)
]


def get_enrichment_pause() -> Callable[[float], None]:
    return time.sleep


def get_enrich_pending_players_use_case(
    provider: MarketValueProviderDep,
    repository: PlayerRepositoryDep,
    pause: Annotated[Callable[[float], None], Depends(get_enrichment_pause)],
) -> EnrichPendingPlayersUseCase:
    return EnrichPendingPlayersUseCase(provider, repository, pause)


EnrichPendingPlayersUseCaseDep = Annotated[
    EnrichPendingPlayersUseCase, Depends(get_enrich_pending_players_use_case)
]


def get_player_percentiles_use_case(
    repository: PlayerRepositoryDep,
) -> GetPlayerPercentilesUseCase:
    return GetPlayerPercentilesUseCase(repository)


GetPlayerPercentilesUseCaseDep = Annotated[
    GetPlayerPercentilesUseCase, Depends(get_player_percentiles_use_case)
]


def get_record_enrichment_use_case(
    repository: PlayerRepositoryDep,
) -> RecordEnrichmentUseCase:
    return RecordEnrichmentUseCase(repository)


RecordEnrichmentUseCaseDep = Annotated[
    RecordEnrichmentUseCase, Depends(get_record_enrichment_use_case)
]


def get_shot_repository(session: SessionDep) -> SqlAlchemyShotRepository:
    return SqlAlchemyShotRepository(session)


ShotRepositoryDep = Annotated[SqlAlchemyShotRepository, Depends(get_shot_repository)]


def get_shot_provider() -> UnderstatShotProvider:
    return UnderstatShotProvider(UnderstatClient(httpx.Client()))


def get_shot_pause() -> Callable[[float], None]:
    return time.sleep


def get_ingest_season_shots_use_case(
    provider: Annotated[UnderstatShotProvider, Depends(get_shot_provider)],
    repository: ShotRepositoryDep,
    pause: Annotated[Callable[[float], None], Depends(get_shot_pause)],
) -> IngestSeasonShotsUseCase:
    return IngestSeasonShotsUseCase(provider, repository, pause)


IngestSeasonShotsUseCaseDep = Annotated[
    IngestSeasonShotsUseCase, Depends(get_ingest_season_shots_use_case)
]


def get_merge_duplicate_players_use_case(
    repository: PlayerRepositoryDep,
) -> MergeDuplicatePlayersUseCase:
    return MergeDuplicatePlayersUseCase(repository)


MergeDuplicatePlayersUseCaseDep = Annotated[
    MergeDuplicatePlayersUseCase, Depends(get_merge_duplicate_players_use_case)
]


def get_find_twins_use_case(
    repository: PlayerRepositoryDep, shots: ShotRepositoryDep
) -> FindTwinsUseCase:
    return FindTwinsUseCase(repository, shots=shots)


FindTwinsUseCaseDep = Annotated[FindTwinsUseCase, Depends(get_find_twins_use_case)]
