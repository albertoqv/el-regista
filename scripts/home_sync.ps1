<#
Lee Transfermarkt desde este PC y manda los resultados a la API de producción.

Transfermarkt bloquea las IPs de centros de datos (GitHub, Vercel) con su WAF desde
oct 2026, pero no una conexión doméstica. Lo lanza la tarea programada que crea
scripts/home_sync_install.ps1; también se puede ejecutar a mano.

Necesita la variable de usuario INGESTION_API_KEY (la guarda el instalador).
Registro: .cache\home-sync.log
#>
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Log = Join-Path $Root ".cache\home-sync.log"
New-Item -ItemType Directory -Force (Split-Path $Log) | Out-Null

$env:API_BASE_URL = "https://el-regista-api.vercel.app"
if (-not $env:INGESTION_API_KEY) {
    $env:INGESTION_API_KEY = [Environment]::GetEnvironmentVariable("INGESTION_API_KEY", "User")
}
if (-not $env:INGESTION_API_KEY) {
    "$(Get-Date -Format s) Falta INGESTION_API_KEY: ejecuta scripts\home_sync_install.ps1" | Add-Content $Log
    exit 1
}

Set-Location $Root
# Scheduled tasks start with a short PATH: find uv where its installer puts it.
$uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $uv) { $uv = Join-Path $env:USERPROFILE ".local\bin\uv.exe" }
"$(Get-Date -Format s) Inicio" | Add-Content $Log
# The 28 leagues: season in progress, and the previous one where the API lacks it.
& $uv run python scripts/scrape_leagues_remote.py --backfill *>> $Log
# Big five leagues, Europe and domestic cups of the season in progress, per competition.
& $uv run python scripts/scrape_competitions_remote.py *>> $Log
# National teams: Nations League, qualifiers, tournaments and friendlies (150 pages a run).
& $uv run python scripts/scrape_national_teams_remote.py *>> $Log
# Photos, birth dates and market values of the players still pending (most are done:
# a smaller batch keeps the night's pages within what Transfermarkt tolerates).
& $uv run python scripts/enrich_remote.py --limit 150 *>> $Log
"$(Get-Date -Format s) Fin" | Add-Content $Log
