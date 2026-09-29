from __future__ import annotations

from fastapi import APIRouter

from player_scouting.presentation.api.dependencies import (
    EnrichPlayerMarketValueUseCaseDep,
    IngestCompetitionUseCaseDep,
    IngestPlayerSeasonUseCaseDep,
)
from player_scouting.presentation.api.schemas import (
    IngestionResultOut,
    ingestion_result_out_from_domain,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post(
    "/statsbomb/{competition_id}/{season_id}", response_model=IngestionResultOut
)
def ingest_statsbomb_competition(
    competition_id: int,
    season_id: int,
    use_case: IngestCompetitionUseCaseDep,
) -> IngestionResultOut:
    result = use_case.execute(competition_id, season_id)
    return ingestion_result_out_from_domain(result)


@router.post("/api-football/players", response_model=IngestionResultOut)
def ingest_api_football_player(
    name: str,
    league: int,
    season: int,
    use_case: IngestPlayerSeasonUseCaseDep,
) -> IngestionResultOut:
    result = use_case.execute(name, league_id=league, season_year=season)
    return ingestion_result_out_from_domain(result)


@router.post("/transfermarkt/players", response_model=IngestionResultOut)
def ingest_transfermarkt_player(
    player_id: int,
    name: str,
    use_case: EnrichPlayerMarketValueUseCaseDep,
) -> IngestionResultOut:
    result = use_case.execute(player_id, name)
    return ingestion_result_out_from_domain(result)
