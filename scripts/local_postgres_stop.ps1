<#
Detiene el PostgreSQL local portable arrancado con local_postgres_start.ps1.

Uso:
    .\scripts\local_postgres_stop.ps1
#>

$PgBin = "C:\tools\pgsql-portable\pgsql\bin"
$PgData = "C:\tools\pgsql-portable\pgsql\data"

& "$PgBin\pg_ctl.exe" -D $PgData stop
