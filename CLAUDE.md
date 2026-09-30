# TalentScope (player-scouting)

App de usuario para comparar futbolistas y encontrar jugadores parecidos, con datos
reales de las 5 grandes ligas. Proyecto personal: **todo debe ser 100% gratis**
(no proponer planes de pago como solución).

## Stack y estructura

- Backend: Python 3.14, FastAPI, SQLAlchemy 2 (sync), Alembic, PostgreSQL, httpx, uv.
  Clean Architecture en `src/player_scouting/`:
  - `domain/` — `Player` (date_of_birth opcional + `birth_year`), `Season`
    (`start_year`), `Statistics` (+ `with_advanced`), `AdvancedStatistics`,
    `SimilarityCalculator` (ignora `minutes_played`).
  - `application/` — puertos en `ports.py`, casos de uso en `use_cases/`,
    cruce de jugadores entre fuentes en `player_matching.py`.
  - `infrastructure/` — un paquete por fuente con patrón client/mapper/provider:
    `fbref_kaggle/`, `understat/`, `transfermarkt/`, `statsbomb/`, `api_football/`,
    `birth_dates/` (Wikidata); `persistence/` (modelos + repositorios).
  - `presentation/api/` — routers `players` e `ingestion` (todo `/ingestion/*`
    exige cabecera `X-Ingestion-Key` si `INGESTION_API_KEY` está configurada).
- Web: `web/` Next.js 16 (App Router, lee `web/AGENTS.md`: APIs cambiadas respecto
  a lo conocido), Tailwind, iconos SVG propios en `web/app/components/icons.tsx`,
  color de marca `#2a78d6`. No hay pantalla de ingesta (es solo API).

## Comandos

```bash
uv run pytest                 # tests; los de persistencia se saltan sin DATABASE_URL
uv run mypy && uv run ruff check .
# Postgres local portátil (puerto 5433):
#   scripts/local_postgres_start.ps1 / local_postgres_stop.ps1
DATABASE_URL="postgresql+psycopg://scouting:scouting@localhost:5433/scouting" uv run pytest
uv run alembic upgrade head
cd web && npx tsc --noEmit && npm run lint && npm run build
```

## Convenciones

- TDD estricto; commits en español, Conventional Commits, en pareja por capa:
  `test: X` y luego `feat: X` (también `fix:`, `refactor:`, `style:`, `docs:`).
- ruff line-length 88. En Python 3.14 `except A, B:` sin paréntesis es válido
  (PEP 758); `ruff format` lo escribe así, no es un bug.
- Tests de proveedores con fixtures pequeñas copiadas de respuestas reales
  (`httpx.MockTransport`); dobles en `tests/application/doubles.py` (el
  `InMemoryPlayerRepository` debe imitar al de SQL, incluida la fusión de avanzadas).
- Nunca inventar URLs ni IDs de entidades externas: descubrirlos con una búsqueda o
  un enlace real antes de usarlos.

## Fuentes de datos (verificadas en vivo, sept 2026)

- **FBref vía Kaggle** (fuente principal): `hubertsidorowicz/football-players-stats-{Y}-{Y+1}`,
  descarga sin cuenta, se regenera cada lunes. 26/27 y 25/26 solo métricas básicas;
  24/25 completas (xG, pases, regates, toques por zona). Sin ID ni fecha exacta:
  ID = hash de nombre+año de nacimiento en [1e9, 2^31).
- **Understat** (xG, xA, pases clave, xGChain, xGBuildup; tiros con X/Y en
  `getPlayerData/{id}`): su robots.txt prohíbe bots; el usuario aceptó el riesgo con
  volumen mínimo. Se guardan aparte (`player_season_advanced_stats`) para que el
  refresco de FBref no las pise.
- **Transfermarkt**: foto, fecha de nacimiento, pie y valor de mercado (robots.txt lo
  permite). Elegir candidato por edad y nombre, nunca el primero a ciegas. Si
  responde 403/429 → `EnrichmentUnavailableError` (parar el lote, no marcar a nadie).
- **API-Football**: cuenta gratuita suspendida (IP compartida de Railway). Código
  conservado pero sin cron. **StatsBomb**: 21 jugadores históricos de 1984.

## Producción

- API: Railway, servicio `api` (https://api-production-5ac3.up.railway.app); las
  migraciones corren solas al arrancar. `npx @railway/cli up --service api --detach`.
  El estado de despliegue de la CLI va con retraso: comprobar la API en vivo.
  La BD solo es accesible por red privada: limpiezas de datos = migración de Alembic.
- Web: Vercel (https://web-seven-tan-39.vercel.app). `cd web && npx vercel --prod --yes`.
- Secretos solo como variables de entorno (Railway / GitHub secrets
  `API_BASE_URL`, `INGESTION_API_KEY`); nunca en ficheros del repo.
- `.github/workflows/weekly-fbref-refresh.yml`: martes, FBref + Understat de la
  temporada en curso y 200 jugadores de Transfermarkt.

## Trampas del entorno (Windows)

- `pkill` desde bash no mata el `python.exe` de uvicorn: usar PowerShell
  `Get-NetTCPConnection -LocalPort 8000 | % { Stop-Process -Id $_.OwningProcess -Force }`.
  Un uvicorn viejo en el 8000 sirve código antiguo.
- `/tmp` de bash no lo ve el Python de Windows: usar el directorio scratchpad con
  rutas `C:\...`.
- Los tests de persistencia fallan si la BD local tiene datos de pruebas manuales:
  vaciar tablas antes.

## Trabajo en curso

Completado (2026-09-30): fotos, fecha exacta y valor de mercado desde Transfermarkt
(`POST /ingestion/transfermarkt/enrich?limit=25`, más relevantes primero, marca
`enrichment_checked_at`) y métricas avanzadas desde Understat
(`POST /ingestion/understat/seasons/{año}`, cruce ~96%). El workflow semanal hace
FBref → Understat → 8 lotes de Transfermarkt.

Siguiente (fase 2, secundaria): métricas por 90', mapas de tiro y pie con
`getPlayerData/{understat_id}`, rediseño visual con animaciones y pantalla de
enfrentamiento en el comparador (no hay imágenes gratuitas de cuerpo entero).
