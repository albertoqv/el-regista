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
"$(Get-Date -Format s) Inicio" | Add-Content $Log
# The 28 leagues: season in progress, and the previous one where the API lacks it.
uv run python scripts/scrape_leagues_remote.py --backfill *>> $Log
# Photos, birth dates and market values of the players still pending.
uv run python scripts/enrich_remote.py --limit 400 *>> $Log
"$(Get-Date -Format s) Fin" | Add-Content $Log
