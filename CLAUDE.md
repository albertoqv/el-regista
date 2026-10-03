# El Regista (player-scouting, antes TalentScope)

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
  a lo conocido), Tailwind. **Marca El Regista** (tema claro): papel #F7F6F2, tinta #16171B, naranja balón #C93C17
  (acento y Scout) y azul #2350D8 (Pronósticos, jugador/local A) (tokens en `globals.css`).
  Nada de verde+amarillo (casa de apuestas) ni granate; sin iconos en menús, sin puntitos
  de color, sin rótulos pequeños en mayúsculas espaciadas; texto mínimo 13 px (`--text-xs`).
  Tipografía: **Regista Display** propia (solo mayúsculas) para titulares ≥3xl y cifras;
  **Schibsted Grotesk** (`font-heading`, negrita) para títulos pequeños y menús, y para el
  texto. Texto sobre fotos: clase `photo-header`/`on-photo` (lo fuerza a claro).
  Logo, iconos y fuente se generan con `scripts/brand/*.py` (shapely + fontTools) →
  `web/app/fonts/`, `web/public/brand/`, `web/app/components/icons.tsx` (no editar a mano).
  Nada de efectos "de IA" (notas manuscritas, brillos, degradados, cristal) y poco texto.
  Fotos libres en `web/public/photos` con créditos en `lib/photos.ts` (pie de página).
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

- **Todo gratis desde oct 2026** (antes Railway, en plan de prueba): API en Vercel, proyecto
  `el-regista-api` (https://el-regista-api.vercel.app; entrypoint `index.py` en la raíz,
  `vercel.json` con framework fastapi, `.vercelignore` deja fuera web/tests/scripts), desde la
  raíz `npx vercel deploy --prod --yes`. Al ver `VERCEL=1` la API exige clave y oculta /docs.
  BD en **Neon** (plan Free, Frankfurt, integración de Vercel: `DATABASE_URL` en el proyecto y
  secreto `DATABASE_URL` de GitHub = conexión sin pooler). Vercel enmascara esas variables al
  hacer `env pull` ([SENSITIVE]): lo que necesite la BD se hace desde GitHub Actions.
  Las migraciones NO corren al desplegar: las aplica el refresco (`alembic upgrade head`).
  Límite de 5 min por función: la ingesta corre en el runner con una API local sobre Neon.
  Estado en memoria (caché, métricas, errores del navegador) es por instancia de Vercel.
  **Trampa**: el proyecto `web` de Vercel tiene la integración de GitHub apuntando a la raíz;
  el `vercel.json` raíz lleva `"git": {"deploymentEnabled": false}` porque si no cada push
  publicaba la API (FastAPI) en elregista.vercel.app. Web y API se despliegan solo por CLI.
- Web: Vercel (https://elregista.vercel.app; el antiguo web-seven-tan-39 redirige). `cd web && npx vercel --prod --yes`.
  El navegador llama a la API por `/api/*` (rewrite en `next.config.ts`): sin CORS en ningún dominio.
  URL pública en `web/lib/site.ts` (`NEXT_PUBLIC_SITE_URL`).
- Secretos solo como variables de entorno (Vercel / GitHub secrets `DATABASE_URL`,
  `API_BASE_URL`, `INGESTION_API_KEY`); nunca en ficheros del repo. Copias: `scripts/db_copy.py`.
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
- Explorador con 9 ligas más (solo goles/asistencias/minutos/tarjetas). El dataset de
  Kaggle se queda en la última temporada terminada: la temporada en curso sale de las
  páginas de club de Transfermarkt (`transfermarkt/league_pages.py`,
  `scripts/scrape_leagues_remote.py` desde el runner → `POST /ingestion/transfermarkt/league-seasons`).
- **Dos productos** (`web/lib/products.ts`, fuente única de menú, pestañas, portada y pie):
  Scout (`/buscar`, `/explorar`, `/gemelos`, `/compare`, `/en-racha`) y Pronósticos
  (`/predicciones`, `/predicciones/historial`, `/equipos`). El menú móvil va fuera del
  `<header>` (su backdrop-blur recorta hijos `fixed`).
- **Historial de aciertos**: `SnapshotPredictionsUseCase` guarda modelo, mercado y +2,5
  de los próximos 7 días (`POST /ingestion/predictions/snapshot`, tabla
  `prediction_snapshots`, migración 0016; paso del workflow) y solo toca partidos sin
  empezar. `GET /predictions/track-record` puntúa lo guardado + la temporada
  reconstruida con `BacktestUseCase.scored_matches`. 26/27 reconstruida: 49% 1X2, 87%
  con ≥60%. Parón FIFA unificado sept-oct: sin partidos del 20 sept al 9 oct 2026.
- **En racha** (`GET /players/hot`, plantillas de Understat): G+A, goles, xG+xA o
  mejora sobre su media; mínimo 180'. Imagen en `/en-racha/card`.
- Coste: Dockerfile con `exec uvicorn` y `MALLOC_ARENA_MAX=2`; pool con `pre_ping`;
  la web reintenta 502/503/504 una vez y cachea 30 min (listo para Serverless de Railway).
- **Técnica (oct 2026)**: Lighthouse en producción: accesibilidad 100, buenas prácticas 100,
  SEO 100 (la ficha de jugador marca 83 por los metadatos en streaming, pero bots y redes
  los reciben en `<head>`); rendimiento ~80-90 en móvil lento. `Reveal` es un componente de
  servidor (`components/Reveal.tsx`) y las animaciones de portada son CSS (`rise-in`,
  `grow-x`, `dropdown-in`): no importar `motion` en componentes de la portada. Fotos propias
  con `next/image`; la foto principal del jugador con `priority` + `preconnect`.
- Auditoría responsive: `scratchpad/audit.py`-style (CDP, 390/768/1024, detectar
  `scrollX` real; el `overflow: clip` del body esconde culpables).

- **Bloques SEO, técnica, datos y legal** (2026-10-03):
  - `/aviso-legal`, `/privacidad`, `/juego-responsable` (+18, enlaces DGOJ verificados;
    jugarbien.es no resuelve). Nota interna de licencias: `docs/fuentes-y-licencias.md`.
  - `/ranking` y `/ranking/[liga]/[metrica]` (14 ligas; las 9 extra solo goles/asistencias),
    JSON-LD (`JsonLd.tsx`: Person, SportsTeam, SportsEvent, ItemList, WebSite), sitemap
    con ~900 URLs (jugadores, equipos, partidos), `/feed.xml` (solo cifras, sin textos).
  - `GET /health/data` (503 si hay partidos de hace 3-14 días sin resultado; se comprueba
    al final del refresco), `GET /ingestion/backup` (volcado COPY en gzip, restaurable con
    `restore_data` o psql tras `alembic upgrade head`), caché GET en memoria (32 MB, 10 min,
    se vacía con cualquier POST /ingestion; cabecera `X-Cache`).
  - Workflows: `monitor.yml` (cada 3 h, no más para no despertar la API serverless),
    `backup.yml` (domingos, artefacto 90 días), `web-quality.yml` (Playwright `web/e2e`
    contra producción + Lighthouse CI con `web/lighthouserc.json`).
  - Gemelos básicos: si el objetivo no tiene perfil de estilo (<5 métricas), compara goles
    y asistencias con el mismo rol detallado (`basic` en la API, aviso en la web).
  - Modelo: probados descanso entre partidos (solo vemos liga, no copas: sobreajusta) y
    vida media 60-240 días (mejora ≤0,001, dentro del ruido por bootstrap). No se cambia.

- **Seguridad, fidelidad, gemelos por rol y tendencias** (2026-10-03):
  - API: `require_ingestion_key`/`expose_docs` (el Dockerfile los pone a true/false),
    `hmac.compare_digest`, bloqueo tras 10 claves fallidas por IP (15 min), límite por IP
    (`rate_limit_per_minute`, 600; última IP de X-Forwarded-For), `POST /admin/session` →
    token firmado de 7 días (la web guarda el token, no la clave). `create_app(settings)`.
  - Web: CSP y cabeceras en `next.config.ts` (connect-src incluye la API para las visitas);
    el rewrite `/api/*` excluye ingestion/admin/docs. CI: `pip-audit` + `npm audit`; Dependabot.
    e2e que falla con cualquier error de consola (detecta violaciones de CSP).
  - Datos: `application/team_names.py` aprende nombres de equipo de Understat al cruzar
    jugadores y renombra los de FBref (`rename_season_team`); `/health/data` lista goles que
    no cuadran FBref/Understat (informativo); `latest_season_year` también en `/players/{id}`.
  - Gemelos: `domain/roles.py` (grafo de roles de Transfermarkt): penalización 0/4/10/20 por
    distancia, roles híbridos (distancia 1) cruzan posición, `role_match` en la API y la web.
  - Tendencias: `domain/trends.py` + `GET /players/{id}/trend` (líneas de Understat, media
    móvil 5 partidos por 90, dirección ±20%) → `TrendChart` en la ficha (ejes en HTML).
  - Rankings: filtro de ligas en dos grupos; si la temporada actual no tiene datos, enseña
    la última terminada y lo dice en el título.

- **Laboratorio de modelos**: skill `.claude/skills/model-lab` + `scripts/model_lab.py`
  (base de datos `scouting_lab`, que los tests no tocan; caché por variante en
  `.cache/model_lab/`, reanudable; largo → `scripts/model_lab_background.ps1`, proceso aparte
  que sobrevive a la sesión). `team_ratings(priors=..., prior_matches=...)` permite que un
  equipo (p. ej. ascendido) se encoja hacia su propia referencia.

- **33 ligas, panel y rendimiento** (2026-10-03):
  - `SEASON_LEAGUES` (28): las 9 del dataset + A1, C1, PL1, TS1, KR1, RO1, SER1, SA1, MEX1, AUS1
    + segundas GB2, GB3, ES2, IT2, L2, L3, FR2, NL2, PO2 (códigos leídos de las páginas de país
    de Transfermarkt). Las de año natural (BRA, MLS, ARG, JAP, KOR, NOR, SWE) fuera: su
    temporada no encaja con "2026 = 26/27". El scraper con `--backfill` rellena la temporada
    anterior solo si la API no la tiene. Web: `SECOND_DIVISIONS` en `lib/format.ts`, grupo
    "Segundas" en rankings (`LEAGUE_GROUPS` en `lib/rankings.ts`).
  - Panel: `POST /metrics/error` (errores del navegador en memoria, agrupados; `ErrorReporter`
    + `error.tsx`) y `data_quality` en `/admin/dashboard`.
  - CI: job `web-e2e` (build local contra la API real + Playwright) antes de desplegar.
  - `/predicciones` enseña 4 días naturales desde el primer partido; el resto con `?todos=1`.
  - Modelo: vida media 180 días (laboratorio); ascendidos, Elo, calibración y empates descartados.

Ideas siguientes: lesiones/alineaciones (no hay fuente
gratuita fiable), producto (cuentas, favoritos, alertas, planes).
No hay fuente gratuita de fotos de cuerpo entero.
