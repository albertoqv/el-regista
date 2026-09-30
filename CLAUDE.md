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
  estética oscura (tokens en `globals.css`: `brand`, `side-a` azul, `side-b` naranja),
  animaciones con `motion` (`motion/react`), fotos grandes vía `bigPhoto()`
  (Transfermarkt `/portrait/big/`). Métricas y textos explicativos en `web/lib/metrics.ts`.
  No hay pantalla de ingesta (es solo API).
  Trampas: SVG calculado en servidor → redondear coordenadas (hidratación); `<title>`
  de SVG con un único string; headless Chrome en Windows no baja de ~500px de ancho.

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
- `.github/workflows/weekly-fbref-refresh.yml`: martes y viernes: FBref, Understat
  (jugadores, equipos/calendario, tiros), dataset de Transfermarkt, fusión de
  duplicados y 400 jugadores de Transfermarkt desde el runner.

## Trampas del entorno (Windows)

- `pkill` desde bash no mata el `python.exe` de uvicorn: usar PowerShell
  `Get-NetTCPConnection -LocalPort 8000 | % { Stop-Process -Id $_.OwningProcess -Force }`.
  Un uvicorn viejo en el 8000 sirve código antiguo.
- `/tmp` de bash no lo ve el Python de Windows: usar el directorio scratchpad con
  rutas `C:\...`.
- Los tests de persistencia fallan si la BD local tiene datos de pruebas manuales:
  vaciar tablas antes.

## Trabajo en curso

Hecho (2026-09-30), además de lo anterior:
- **Gemelos 2.0**: el perfil de tiro (tramo final, cabeza, lejos, balón parado,
  definición, xG/tiro) entra en la similitud; mini-radar por gemelo.
- **Explorador** (`GET /players/explore`, web `/explorar`) con recetas.
- **Carta compartible** (`web/app/players/[id]/card/route.tsx`, `next/og`) + OG.
- **Dataset Transfermarkt** (Kaggle `davidcariboo/player-scores`, sin cuenta):
  fotos/altura/posición detallada/valores para ~92% de jugadores y 9 ligas más con
  stats por jugador (TR, PO, NL, BE, SC, GR, DK, UKR, RU; el resto de ligas del
  dataset no trae apariciones). Ids nuevos = 500_000_000 + id de Transfermarkt.
- **Equipos y predicciones** (Understat `getLeagueData`: `teams.history` y `dates`,
  migración 0012): `/teams/table|matches|players`, `/predictions`,
  `/predictions/backtest`. Modelo Poisson + Dixon-Coles con fuerzas por xG
  (`domain/prediction.py`), parámetros afinados en 24/25 y validados en 25/26:
  Brier 0,594 (referencia 0,649), acierto 52%, bien calibrado. Horas de Understat en
  UTC (la web las muestra en Europe/Madrid).
- Web: `/equipos`, `/equipos/[team]`, `/predicciones`, `/como-funciona`.

- **Predicciones ampliadas** (2026-09-30):
  - football-data.co.uk (`infrastructure/football_data/`, tabla `match_stats`,
    migración 0013): córners, tarjetas, faltas, tiros, descanso y cuotas por partido;
    `fixtures.csv` trae próximos partidos con árbitro y cuotas. Nombres de equipo
    distintos a Understat: `learn_team_names` los empareja por fecha ±1 y marcador.
  - `domain/counts.py`: binomial negativa por equipo (a favor/en contra), encogimiento
    10 partidos (afinado en 24/25, validado en 25/26). Córners/faltas/tiros mejoran a la
    media de liga; amarillas ≈ media (árbitro solo en la Premier).
  - `application/use_cases/match_insights.py`: análisis completo (`/predictions/{id}/insights`),
    backtest de estadísticas y `HighlightsUseCase` (`/predictions/highlights`: lo más
    probable de la próxima jornada, mercados de referencia). Caché por liga.
  - Plantillas Understat por partido (`player_match_stats`, migración 0014; hay
    jugadores repetidos en alguna plantilla → se deduplica). `domain/player_props.py` +
    `player_markets.py`: marca/asiste/amarilla/tiros **si juega** + probabilidad de jugar
    (`/predictions/{id}/players`, `/predictions/players-backtest`).
  - Web: `/predicciones/[match]` (análisis completo), destacadas en predicciones y
    portada, cifras reales (`GET /overview`). `Reveal` es CSS puro (nunca oculta
    contenido sin JS).
- Workflow semanal reescrito con funciones `post`/`until_done`; lotes de plantillas de 40
  (con 120 Railway corta la petición).

- **1X2 frente al mercado** (`MarketBenchmarkUseCase`, `/predictions/market-benchmark`):
  en 25/26 cuotas de cierre 0,582 < modelo 0,594 y toda mezcla empeora al mercado →
  con cuotas, el 1X2 principal es el del mercado.

- **Marca/asiste/amarilla son "si juega"** + `plays`: así la calibración de "marca" es
  casi perfecta (La Liga 25/26, 10.840 pronósticos, Brier 0,067 vs 0,074; ningún
  factor de corrección la mejora).

- **Panel `/admin`** (2026-09-30): entra con la `INGESTION_API_KEY` (cookie httpOnly).
  Visitas propias sin cookies ni IP (`POST /metrics/visit` en text/plain, hash diario con
  sal; bots y `/admin` excluidos; tabla `page_views`, migración 0015), salud de la API en
  memoria desde el último despliegue, datos y coste de Railway (`infrastructure/railway/`,
  mismas consultas y precios que `railway usage`; necesita `RAILWAY_API_TOKEN` +
  `RAILWAY_WORKSPACE_ID` en el servicio `api`, si no muestra "sin conectar"). También
  `@vercel/analytics` (activar Analytics en el panel de Vercel). `GET /health` público.
  Coste medido: ~0,11 $/día, casi todo memoria.
- Explorador con 9 ligas más (solo goles/asistencias/minutos/tarjetas, hasta 25/26).

Ideas siguientes: lesiones/alineaciones (no hay fuente
gratuita fiable), producto (cuentas, favoritos, alertas, planes).
No hay fuente gratuita de fotos de cuerpo entero.
