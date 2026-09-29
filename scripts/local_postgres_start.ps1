<#
Arranca un PostgreSQL local sin necesitar Docker ni permisos de administrador,
usando los binarios portables instalados en C:\tools\pgsql-portable.

Uso:
    .\scripts\local_postgres_start.ps1

Deja el servidor escuchando en localhost:5433 con la base de datos "scouting"
ya creada. La cadena de conexión resultante es la misma que .env.example:

    postgresql+psycopg://scouting:scouting@localhost:5433/scouting
#>

$PgBin = "C:\tools\pgsql-portable\pgsql\bin"
$PgData = "C:\tools\pgsql-portable\pgsql\data"

if (-not (Test-Path $PgData)) {
    Write-Error "No se encuentra $PgData. Este script asume que ya se ejecutó initdb (ver README)."
    exit 1
}

& "$PgBin\pg_ctl.exe" -D $PgData -l "$PgBin\..\logfile.txt" -o "-p 5433" start
