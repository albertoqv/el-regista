from __future__ import annotations

import zlib
from collections.abc import Iterator
from dataclasses import asdict
from datetime import date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.ports import MarketValueHistoryResult
from player_scouting.application.use_cases.market_valuation import (
    EstimateMarketValuesUseCase,
)
from player_scouting.application.use_cases.track_record import (
    SnapshotPredictionsUseCase,
)
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.infrastructure.transfermarkt.league_pages import SEASON_LEAGUES
from player_scouting.presentation.api.dependencies import (
    BackupStream,
    CompetitionStatsRepositoryDep,
    EnqueueLeagueIngestionUseCaseDep,
    EnrichFromDatasetUseCaseDep,
    EnrichPendingPlayersUseCaseDep,
    EnrichPlayerMarketValueUseCaseDep,
    IngestAdvancedSeasonUseCaseDep,
    IngestCompetitionUseCaseDep,
    IngestDatasetCompetitionsUseCaseDep,
    IngestDatasetLeaguesUseCaseDep,
    IngestMatchStatsUseCaseDep,
    IngestPlayerSeasonUseCaseDep,
    IngestRostersUseCaseDep,
    IngestScrapedLeagueSeasonUseCaseDep,
    IngestSeasonDatasetUseCaseDep,
    IngestSeasonShotsUseCaseDep,
    IngestTeamSeasonUseCaseDep,
    LeagueIngestionJobRepositoryDep,
    LeagueSearchProviderDep,
    MatchStatsRepositoryDep,
    MergeDuplicatePlayersUseCaseDep,
    PlayerRepositoryDep,
    PredictionLogDep,
    ProcessLeagueIngestionBatchUseCaseDep,
    RecordCompetitionLinesUseCaseDep,
    RecordEnrichmentUseCaseDep,
    TeamRepositoryDep,
    ValueEstimateRepositoryDep,
    get_backup_stream,
)
from player_scouting.presentation.api.schemas import (
    CompetitionLinesIn,
    EnrichmentIn,
    IngestionResultOut,
    LeagueIngestionBatchSummaryOut,
    LeagueIngestionJobOut,
    LeagueSummaryOut,
    PendingEnrichmentOut,
    ScrapedLeagueSeasonIn,
    ShotIngestionSummaryOut,
    TeamSeasonSummaryOut,
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


@router.get("/backup")
def download_backup(
    stream: Annotated[BackupStream, Depends(get_backup_stream)],
) -> StreamingResponse:
    """Every table as a gzipped, psql-replayable dump (weekly GitHub Action)."""

    def gzipped() -> Iterator[bytes]:
        compressor = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        for chunk in stream():
            if data := compressor.compress(chunk):
                yield data
        yield compressor.flush()

    filename = f"elregista-{date.today().isoformat()}.sql.gz"
    return StreamingResponse(
        gzipped(),
        media_type="application/gzip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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


@router.post("/fbref/seasons/{start_year}", response_model=IngestionResultOut)
def ingest_fbref_season(
    start_year: int,
    use_case: IngestSeasonDatasetUseCaseDep,
) -> IngestionResultOut:
    result = use_case.execute(start_year)
    return ingestion_result_out_from_domain(result)


@router.post("/understat/seasons/{start_year}", response_model=IngestionResultOut)
def ingest_understat_season(
    start_year: int,
    use_case: IngestAdvancedSeasonUseCaseDep,
) -> IngestionResultOut:
    result = use_case.execute(start_year)
    return ingestion_result_out_from_domain(result)


@router.post("/understat/shots/{start_year}", response_model=ShotIngestionSummaryOut)
def ingest_understat_shots(
    start_year: int,
    use_case: IngestSeasonShotsUseCaseDep,
    limit: Annotated[int, Query(ge=1, le=400)] = 80,
) -> ShotIngestionSummaryOut:
    summary = use_case.execute(start_year, limit)
    return ShotIngestionSummaryOut(
        matches=summary.matches, shots=summary.shots, remaining=summary.remaining
    )


@router.post("/maintenance/merge-duplicates")
def merge_duplicate_players(
    use_case: MergeDuplicatePlayersUseCaseDep,
) -> dict[str, int]:
    return {"merged": use_case.execute()}


@router.post("/transfermarkt-dataset/profiles", response_model=IngestionResultOut)
def enrich_from_transfermarkt_dataset(
    use_case: EnrichFromDatasetUseCaseDep,
) -> IngestionResultOut:
    return ingestion_result_out_from_domain(use_case.execute())


@router.post(
    "/transfermarkt-dataset/seasons/{start_year}", response_model=IngestionResultOut
)
def ingest_transfermarkt_dataset_season(
    start_year: int, use_case: IngestDatasetLeaguesUseCaseDep
) -> IngestionResultOut:
    return ingestion_result_out_from_domain(use_case.execute(start_year))


@router.post("/transfermarkt-dataset/competitions", response_model=IngestionResultOut)
def ingest_transfermarkt_dataset_competitions(
    use_case: IngestDatasetCompetitionsUseCaseDep,
) -> IngestionResultOut:
    """Europe, cups, super cups and national teams of the finished seasons."""
    return ingestion_result_out_from_domain(use_case.execute())


@router.post("/transfermarkt/competition-lines", response_model=IngestionResultOut)
def receive_competition_lines(
    body: CompetitionLinesIn, use_case: RecordCompetitionLinesUseCaseDep
) -> IngestionResultOut:
    """The season in progress of Europe, cups and the big leagues, read at home."""
    return ingestion_result_out_from_domain(use_case.execute(body.to_domain()))


@router.post("/valuations")
def estimate_market_values(
    players: PlayerRepositoryDep,
    competitions: CompetitionStatsRepositoryDep,
    estimates: ValueEstimateRepositoryDep,
) -> dict[str, Any]:
    """Refits the market value model and stores every player's estimate."""
    return asdict(
        EstimateMarketValuesUseCase(players, competitions, estimates).execute()
    )


@router.post("/transfermarkt/league-seasons", response_model=IngestionResultOut)
def receive_scraped_league_season(
    body: ScrapedLeagueSeasonIn, use_case: IngestScrapedLeagueSeasonUseCaseDep
) -> IngestionResultOut:
    """26/27 and later of the extra leagues, read from Transfermarkt elsewhere."""
    if body.competition not in SEASON_LEAGUES.values():
        raise HTTPException(status_code=422, detail="Unknown league")
    return ingestion_result_out_from_domain(
        use_case.execute(
            body.competition,
            body.season_label,
            [row.to_domain() for row in body.rows],
        )
    )


@router.post("/understat/teams/{start_year}", response_model=TeamSeasonSummaryOut)
def ingest_understat_teams(
    start_year: int, use_case: IngestTeamSeasonUseCaseDep
) -> TeamSeasonSummaryOut:
    summary = use_case.execute(start_year)
    return TeamSeasonSummaryOut(
        fixtures=summary.fixtures, team_matches=summary.team_matches
    )


# Replaced in tests: forecasts are logged relative to "now".
_now = datetime.now


@router.post("/predictions/snapshot")
def snapshot_predictions(
    teams: TeamRepositoryDep,
    stats: MatchStatsRepositoryDep,
    log: PredictionLogDep,
    days: Annotated[int, Query(ge=1, le=90)] = 7,
) -> dict[str, int]:
    """Log the forecasts of the coming days before kickoff (the track record)."""
    saved = SnapshotPredictionsUseCase(teams, stats, log, now=_now).execute(days)
    return {"saved": saved}


@router.post("/football-data/seasons/{start_year}")
def ingest_football_data(
    start_year: int, use_case: IngestMatchStatsUseCaseDep
) -> dict[str, int]:
    return {"saved": use_case.execute(start_year)}


@router.post("/understat/rosters/{start_year}")
def ingest_understat_rosters(
    start_year: int,
    use_case: IngestRostersUseCaseDep,
    limit: Annotated[int, Query(ge=1, le=400)] = 120,
) -> dict[str, int]:
    summary = use_case.execute(start_year, limit)
    return {
        "matches": summary.matches,
        "players": summary.players,
        "remaining": summary.remaining,
    }


@router.post("/transfermarkt/enrich", response_model=IngestionResultOut)
def enrich_pending_players(
    use_case: EnrichPendingPlayersUseCaseDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 25,
) -> IngestionResultOut:
    result = use_case.execute(limit)
    return ingestion_result_out_from_domain(result)


@router.get("/enrichment/pending", response_model=list[PendingEnrichmentOut])
def list_pending_enrichment(
    repository: PlayerRepositoryDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[PendingEnrichmentOut]:
    return [
        PendingEnrichmentOut(
            player_id=player.player_id, name=player.name, birth_year=player.birth_year
        )
        for player in repository.list_players_pending_enrichment(limit)
    ]


@router.post("/enrichment/{player_id}", status_code=204)
def record_enrichment(
    player_id: int, body: EnrichmentIn, use_case: RecordEnrichmentUseCaseDep
) -> Response:
    result = (
        MarketValueHistoryResult(
            preferred_foot=body.preferred_foot,
            points=[
                MarketValuePoint(point.as_of, point.amount_eur, point.club)
                for point in body.market_values
            ],
            photo_url=body.photo_url,
            date_of_birth=body.date_of_birth,
        )
        if body.found
        else None
    )
    try:
        use_case.execute(player_id, result)
    except PlayerNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=204)


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
