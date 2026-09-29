from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from player_scouting.application.use_cases.compare_players import ComparePlayersUseCase
from player_scouting.application.use_cases.find_similar_players import (
    FindSimilarPlayersUseCase,
)
from player_scouting.application.use_cases.ingest_competition import (
    IngestCompetitionUseCase,
)
from player_scouting.domain.similarity_calculator import SimilarityCalculator
from player_scouting.infrastructure.birth_dates.wikidata_provider import (
    WikidataBirthDateProvider,
)
from player_scouting.infrastructure.persistence.database import get_session
from player_scouting.infrastructure.persistence.sqlalchemy_player_repository import (
    SqlAlchemyPlayerRepository,
)
from player_scouting.infrastructure.statsbomb.client import StatsBombClient
from player_scouting.infrastructure.statsbomb.competition_statistics_provider import (
    StatsBombCompetitionStatisticsProvider,
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


ComparePlayersUseCaseDep = Annotated[
    ComparePlayersUseCase, Depends(get_compare_players_use_case)
]
FindSimilarPlayersUseCaseDep = Annotated[
    FindSimilarPlayersUseCase, Depends(get_find_similar_players_use_case)
]
IngestCompetitionUseCaseDep = Annotated[
    IngestCompetitionUseCase, Depends(get_ingest_competition_use_case)
]
