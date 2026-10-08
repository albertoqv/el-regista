# Historial de cambios

Lo que se ha ido haciendo, con fechas y cifras medidas. No son reglas: las reglas vigentes
están en `CLAUDE.md` y `.claude/rules/`.

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


Ideas descartadas o sin fuente: lesiones/alineaciones (no hay fuente gratuita fiable),
fotos de cuerpo entero (tampoco). Favoritos y alertas: descartados por el usuario.

- **Límite de transferencia de Neon** (2026-10-05): 5 GB/mes agotados en dos días (gemelos y
  pronósticos leían tablas enteras en cada petición, y el CI recorría la web contra producción
  21 veces al día). Caché de lecturas en memoria (3 h), web a 3 h, e2e solo con cambios en
  `web/` y base copiada a un proyecto nuevo de Neon.

- **Vault y DevSecOps** (2026-10-05): secretos de Vault en el stack local (fuente de
  `pydantic-settings` por debajo de las variables). Pipeline de seguridad por fases:
  Semgrep y Bandit, SCA (pip-audit y npm audit; Dependabot con Docker y Compose), gitleaks,
  Trivy (imágenes sin root, en dos etapas, parcheadas y sin pip ni npm: 0 HIGH/CRITICAL) y
  ZAP (cabeceras nosniff y CORP en la API).

- **Por competición, selecciones y consumo de Neon** (2026-10-07): tabla
  `player_competition_stats` (migración 0018) desde el dataset (2019-25/26: liga, Europa,
  copas, supercopas, Mundial) y desde casa (26/27: 5 grandes, Champions, Europa League,
  Conference, copas; selecciones con Nations League, clasificatorios, torneos y amistosos).
  Ficha: sección "Por competición" y "Con su selección". El refresco falló dos días por
  un salto de línea en el secreto `INGESTION_API_KEY` (cabecera HTTP inválida): ahora se
  limpia y los errores de ingesta salen como anotación.

- **Estudio de "errores de cuota"** (2026-10-08, `scripts/research_odds_value.py`): apostar a la
  cuota máxima cuando supera la justa del consenso (media o Pinnacle sin margen) pierde en
  1X2 en las tres temporadas (−8% a −54%) y en más/menos de 2,5 es ruido. No se ofrece como
  producto: las "gangas" de las cuotas máximas casi nunca se pueden apostar.

- **Histórico estático y ahorro de Neon** (2026-10-08): 4,1 de 5 GB de transferencia gastados
  en tres días por refrescos repetidos. El refresco ya no repite el dataset sin cambios, mide
  cada paso y frena si queda poco. Understat 2014-2023 como ficheros estáticos (8,5 MB): el
  cara a cara Messi-Cristiano de cualquier temporada lleva radar.
