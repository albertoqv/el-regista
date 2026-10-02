from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from typing import Annotated

import httpx
from fastapi import Depends
from sqlalchemy.orm import Session

from player_scouting.application.league_ingestion_job import (
    LeagueIngestionJobRepository,
)
from player_scouting.application.ports import (
    HostingUsageProvider,
    PredictionLogRepository,
    VisitRepository,
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
from player_scouting.application.use_cases.explore_players import (
    ExplorePlayersUseCase,
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
from player_scouting.application.use_cases.match_insights import (
    IngestMatchStatsUseCase,
)
from player_scouting.application.use_cases.merge_duplicate_players import (
    MergeDuplicatePlayersUseCase,
)
from player_scouting.application.use_cases.player_markets import IngestRostersUseCase
from player_scouting.application.use_cases.process_league_ingestion_batch import (
    ProcessLeagueIngestionBatchUseCase,
)
from player_scouting.application.use_cases.record_enrichment import (
    RecordEnrichmentUseCase,
)
from player_scouting.application.use_cases.team_analytics import (
    IngestTeamSeasonUseCase,
)
from player_scouting.application.use_cases.transfermarkt_dataset import (
    EnrichFromDatasetUseCase,
    IngestDatasetLeaguesUseCase,
    IngestScrapedLeagueSeasonUseCase,
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
from player_scouting.infrastructure.football_data.client import FootballDataClient
from player_scouting.infrastructure.football_data.provider import (
    FootballDataProvider,
)
from player_scouting.infrastructure.persistence.backup import dump_data
from player_scouting.infrastructure.persistence.database import engine, get_session
from player_scouting.infrastructure.persistence.overview import (
    DataFreshness,
    data_freshness,
    database_overview,
)
from player_scouting.infrastructure.persistence.sqlalchemy_league_ingestion_job_repository import (  # noqa: E501
    SqlAlchemyLeagueIngestionJobRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_match_stats_repository import (  # noqa: E501
    SqlAlchemyMatchStatsRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_player_repository import (
    SqlAlchemyPlayerRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_prediction_log import (
    SqlAlchemyPredictionLog,
)
from player_scouting.infrastructure.persistence.sqlalchemy_shot_repository import (
    SqlAlchemyShotRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_team_repository import (
    SqlAlchemyTeamRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_visit_repository import (
    SqlAlchemyVisitRepository,
)
from player_scouting.infrastructure.railway.provider import RailwayUsageProvider
from player_scouting.infrastructure.statsbomb.client import StatsBombClient
from player_scouting.infrastructure.statsbomb.competition_statistics_provider import (
    StatsBombCompetitionStatisticsProvider,
)
from player_scouting.infrastructure.transfermarkt.client import TransfermarktClient
from player_scouting.infrastructure.transfermarkt.provider import (
    TransfermarktMarketValueProvider,
)
from player_scouting.infrastructure.transfermarkt_dataset.client import (
    TransfermarktDatasetClient,
)
from player_scouting.infrastructure.transfermarkt_dataset.provider import (
    TransfermarktDatasetZipProvider,
)
from player_scouting.infrastructure.understat.client import UnderstatClient
from player_scouting.infrastructure.understat.provider import (
    UnderstatSeasonProvider,
)
from player_scouting.infrastructure.understat.shot_provider import (
    UnderstatShotProvider,
)
from player_scouting.infrastructure.understat.team_provider import (
    UnderstatTeamProvider,
)
from player_scouting.presentation.api.settings import ApiSettings, get_api_settings

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


def get_explore_players_use_case(
    repository: PlayerRepositoryDep,
) -> ExplorePlayersUseCase:
    return ExplorePlayersUseCase(repository)


ExplorePlayersUseCaseDep = Annotated[
    ExplorePlayersUseCase, Depends(get_explore_players_use_case)
]


def get_transfermarkt_dataset_provider() -> TransfermarktDatasetZipProvider:
    return TransfermarktDatasetZipProvider(TransfermarktDatasetClient(httpx.Client()))


TransfermarktDatasetProviderDep = Annotated[
    TransfermarktDatasetZipProvider, Depends(get_transfermarkt_dataset_provider)
]


def get_enrich_from_dataset_use_case(
    provider: TransfermarktDatasetProviderDep, repository: PlayerRepositoryDep
) -> EnrichFromDatasetUseCase:
    return EnrichFromDatasetUseCase(provider, repository)


def get_ingest_dataset_leagues_use_case(
    provider: TransfermarktDatasetProviderDep, repository: PlayerRepositoryDep
) -> IngestDatasetLeaguesUseCase:
    return IngestDatasetLeaguesUseCase(provider, repository)


def get_ingest_scraped_league_season_use_case(
    repository: PlayerRepositoryDep,
) -> IngestScrapedLeagueSeasonUseCase:
    return IngestScrapedLeagueSeasonUseCase(repository)


IngestScrapedLeagueSeasonUseCaseDep = Annotated[
    IngestScrapedLeagueSeasonUseCase,
    Depends(get_ingest_scraped_league_season_use_case),
]


EnrichFromDatasetUseCaseDep = Annotated[
    EnrichFromDatasetUseCase, Depends(get_enrich_from_dataset_use_case)
]
IngestDatasetLeaguesUseCaseDep = Annotated[
    IngestDatasetLeaguesUseCase, Depends(get_ingest_dataset_leagues_use_case)
]


def get_team_repository(session: SessionDep) -> SqlAlchemyTeamRepository:
    return SqlAlchemyTeamRepository(session)


TeamRepositoryDep = Annotated[SqlAlchemyTeamRepository, Depends(get_team_repository)]


def get_team_data_provider() -> UnderstatTeamProvider:
    return UnderstatTeamProvider(UnderstatClient(httpx.Client()))


def get_ingest_team_season_use_case(
    provider: Annotated[UnderstatTeamProvider, Depends(get_team_data_provider)],
    repository: TeamRepositoryDep,
) -> IngestTeamSeasonUseCase:
    return IngestTeamSeasonUseCase(provider, repository)


IngestTeamSeasonUseCaseDep = Annotated[
    IngestTeamSeasonUseCase, Depends(get_ingest_team_season_use_case)
]


def get_match_stats_repository(session: SessionDep) -> SqlAlchemyMatchStatsRepository:
    return SqlAlchemyMatchStatsRepository(session)


MatchStatsRepositoryDep = Annotated[
    SqlAlchemyMatchStatsRepository, Depends(get_match_stats_repository)
]


def get_match_stats_provider() -> FootballDataProvider:
    return FootballDataProvider(FootballDataClient(httpx.Client()))


def get_ingest_match_stats_use_case(
    provider: Annotated[FootballDataProvider, Depends(get_match_stats_provider)],
    repository: MatchStatsRepositoryDep,
) -> IngestMatchStatsUseCase:
    return IngestMatchStatsUseCase(provider, repository)


IngestMatchStatsUseCaseDep = Annotated[
    IngestMatchStatsUseCase, Depends(get_ingest_match_stats_use_case)
]


def get_ingest_rosters_use_case(
    provider: Annotated[UnderstatShotProvider, Depends(get_shot_provider)],
    repository: ShotRepositoryDep,
    pause: Annotated[Callable[[float], None], Depends(get_shot_pause)],
) -> IngestRostersUseCase:
    return IngestRostersUseCase(provider, repository, pause)


IngestRostersUseCaseDep = Annotated[
    IngestRostersUseCase, Depends(get_ingest_rosters_use_case)
]


def get_visit_repository(session: SessionDep) -> VisitRepository:
    return SqlAlchemyVisitRepository(session)


def get_database_overview(session: SessionDep) -> dict[str, int]:
    return database_overview(session)


BackupStream = Callable[[], Iterator[bytes]]


def get_backup_stream() -> BackupStream:
    def stream() -> Iterator[bytes]:
        # Its own connection: the download outlives the request's session.
        # Repeatable read = every table from the same instant.
        with engine.connect().execution_options(
            isolation_level="REPEATABLE READ"
        ) as connection:
            raw = connection.connection.driver_connection
            assert raw is not None  # psycopg, the only driver we use
            yield from dump_data(raw)

    return stream


def get_data_freshness(session: SessionDep) -> DataFreshness:
    # Fixture kick-offs are stored in UTC without a time zone.
    return data_freshness(session, datetime.now(UTC).replace(tzinfo=None))


def get_hosting_usage_provider(
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
) -> HostingUsageProvider | None:
    if not (settings.railway_api_token and settings.railway_workspace_id):
        return None
    return RailwayUsageProvider(
        httpx.Client(), settings.railway_api_token, settings.railway_workspace_id
    )


def get_prediction_log(session: SessionDep) -> PredictionLogRepository:
    return SqlAlchemyPredictionLog(session)


PredictionLogDep = Annotated[PredictionLogRepository, Depends(get_prediction_log)]
