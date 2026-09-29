from __future__ import annotations

from fastapi import APIRouter

from player_scouting.presentation.api.dependencies import IngestCompetitionUseCaseDep
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
