from __future__ import annotations

from fastapi import APIRouter, Depends

from player_scouting.presentation.api.dependencies import (
    EnqueueLeagueIngestionUseCaseDep,
    EnrichPlayerMarketValueUseCaseDep,
    IngestCompetitionUseCaseDep,
    IngestPlayerSeasonUseCaseDep,
    LeagueIngestionJobRepositoryDep,
    LeagueSearchProviderDep,
    ProcessLeagueIngestionBatchUseCaseDep,
)
from player_scouting.presentation.api.schemas import (
    IngestionResultOut,
    LeagueIngestionBatchSummaryOut,
    LeagueIngestionJobOut,
    LeagueSummaryOut,
    ingestion_result_out_from_domain,
    league_ingestion_batch_summary_out_from_domain,
    league_ingestion_job_out_from_domain,
    league_summary_out_from_domain,
)
from player_scouting.presentation.api.security import verify_ingestion_api_key

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"],
    dependencies=[Depends(verify_ingestion_api_key)],
)


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


@router.get("/leagues/search", response_model=list[LeagueSummaryOut])
def search_leagues(q: str, provider: LeagueSearchProviderDep) -> list[LeagueSummaryOut]:
    return [
        league_summary_out_from_domain(league) for league in provider.search_leagues(q)
    ]


@router.post("/leagues", response_model=LeagueIngestionJobOut)
def enqueue_league_ingestion(
    league_id: int,
    league_name: str,
    season_year: int,
    use_case: EnqueueLeagueIngestionUseCaseDep,
) -> LeagueIngestionJobOut:
    job = use_case.execute(league_id, league_name, season_year)
    return league_ingestion_job_out_from_domain(job)


@router.get("/leagues", response_model=list[LeagueIngestionJobOut])
def list_league_ingestion_jobs(
    repository: LeagueIngestionJobRepositoryDep,
) -> list[LeagueIngestionJobOut]:
    return [league_ingestion_job_out_from_domain(job) for job in repository.list_jobs()]


@router.post("/leagues/process", response_model=LeagueIngestionBatchSummaryOut)
def process_league_ingestion_batch(
    use_case: ProcessLeagueIngestionBatchUseCaseDep,
    budget: int = 90,
) -> LeagueIngestionBatchSummaryOut:
    summary = use_case.execute(request_budget=budget)
    return league_ingestion_batch_summary_out_from_domain(summary)
