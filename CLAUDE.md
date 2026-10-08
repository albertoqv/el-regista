# El Regista (player-scouting)

Web de scout de futbolistas (fichas, comparar, gemelos, rankings, valor) con datos reales
de 33 ligas. **Pronósticos está en segundo plano** (desde oct 2026): fuera de menú, portada,
pie y sitemap, con `noindex` (`hidden` en `web/lib/products.ts`); sus URLs siguen vivas y
el refresco ya no baja football-data ni guarda pronósticos. No volver a destacarlo ni
gastar transferencia de Neon en él. Proyecto personal: **todo debe ser 100% gratis** (no proponer planes
de pago como solución). Nada de contenido editorial automático (crónicas, previas,
portada del día). Las reglas de la web están en `.claude/rules/web.md` (se cargan al
tocar `web/`); el historial de cambios, en `docs/historial.md`.

## Stack y estructura

- Backend: Python 3.14, FastAPI, SQLAlchemy 2 (sync), Alembic, PostgreSQL, httpx, uv.
  Clean Architecture en `src/player_scouting/`:
  - `domain/` — entidades y modelos puros: `Player`, `Season`, `Statistics`
    (+ `with_advanced`), `SimilarityCalculator`, `roles.py`, `prediction.py`
    (Poisson + Dixon-Coles), `counts.py`, `player_props.py`, `trends.py`.
  - `application/` — puertos en `ports.py`, casos de uso en `use_cases/`, cruce de
    jugadores entre fuentes en `player_matching.py`, nombres de equipo en `team_names.py`.
  - `infrastructure/` — un paquete por fuente con patrón client/mapper/provider;
    `persistence/` (modelos + repositorios).
  - `presentation/api/` — routers; todo `/ingestion/*` exige `X-Ingestion-Key`.
- Web: `web/` Next.js 16 (ver `.claude/rules/web.md`).

## Comandos

```bash
uv run pytest                 # los de persistencia se saltan sin DATABASE_URL
uv run mypy && uv run ruff check .
DATABASE_URL="postgresql+psycopg://scouting:scouting@localhost:5433/scouting" uv run pytest
uv run alembic upgrade head
cd web && npx tsc --noEmit && npm run lint && npm run build
uv run python scripts/model_lab.py   # experimentos del modelo: skill model-lab
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
- Un cambio del modelo de pronósticos solo se publica si mejora las dos temporadas de
  validación en el laboratorio (bootstrap pareado, p ≥ 0,95).

## Fuentes de datos

- **FBref vía Kaggle** (principal, 5 grandes): `hubertsidorowicz/football-players-stats-{Y}-{Y+1}`,
  sin cuenta, se regenera cada lunes. 26/27 y 25/26 solo métricas básicas; 24/25
  completas. Sin ID ni fecha exacta: ID = hash de nombre+año de nacimiento en [1e9, 2^31).
- **Understat**: xG, xA, pases clave, xGChain, xGBuildup, tiros, equipos, calendario y
  plantillas por partido (horas en UTC). Su robots.txt prohíbe bots; el usuario aceptó
  el riesgo con volumen mínimo. Las avanzadas van aparte (`player_season_advanced_stats`)
  para que el refresco de FBref no las pise.
- **football-data.co.uk** (solo pronósticos; ya no se refresca): córners, tarjetas,
  faltas, tiros y cuotas por partido; nombres de equipo distintos a Understat
  (`learn_team_names`).
- **Transfermarkt**: foto, fecha de nacimiento, pie, valor, y la temporada en curso de
  las 28 ligas extra (`SEASON_LEAGUES`, páginas de club). Dataset de Kaggle
  `davidcariboo/player-scores` para la última terminada (ids = 500_000_000 + id TM).
  Su WAF de AWS bloquea IPs de centros de datos (202 vacío con
  `x-amzn-waf-action: challenge`): el cliente lo trata como `EnrichmentUnavailableError`,
  igual que 403/429 (parar el lote, no marcar a nadie). Corre en el PC del usuario con la
  tarea programada "El Regista - Transfermarkt" (`scripts/home_sync.ps1`, martes/viernes
  21:00; log `.cache/home-sync.log`). Elegir candidato por edad y nombre, nunca el primero.
- **Por competición** (tabla `player_competition_stats`, aparte de las temporadas de liga
  que leen rankings y gemelos): dataset para lo terminado (`/ingestion/transfermarkt-dataset/
  competitions`); en casa, `scrape_competitions_remote.py` (5 grandes, Europa y copas solo
  de clubes de primera) y `scrape_national_teams_remote.py` (selecciones de Mundial y
  Eurocopa; códigos del selector de su página de rendimiento, `.cache/national-teams.json`,
  150 páginas por noche). Los torneos llevan su año (Mundial 2026), lo demás la temporada.
- Las ligas de año natural (Brasil, MLS, Escandinavia...) quedan fuera de rankings y
  gemelos (no encajan con "2026 = 26/27"); sí salen en la ficha por competición, con la
  temporada en la que Transfermarkt las archiva. Quien jugó en las 5 grandes o en Europa
  desde 2019 y no teníamos (Messi) se crea desde el perfil del dataset.
- **Valor estimado** (`domain/valuation.py`): ridge en Python puro sobre log(valor) con edad,
  posición, liga, minutos, goles/asist. por 90, Europa y selección de la última temporada
  terminada; factores multiplicativos frente al jugador medio y error mediano medido con 1 de
  cada 5 jugadores apartado. Se recalcula en el refresco (`/ingestion/valuations`), tablas
  `player_value_estimates` y `value_model`. Web: bloque en la ficha y `/infravalorados`.
- **Carrera por edad** (`domain/career.py`, `/players/{id}/career`): G+A por 90 de club por
  temporada frente a la media de su posición (agregado en SQL, `READ_CACHE`).
- **Buscador**: `f_unaccent` + `pg_trgm` (`word_similarity` ≥ 0,5; migración 0020).
- **Histórico estático** (`web/public/history`, 2014-2023 de las 5 grandes de Understat):
  ficheros por liga y temporada + índice partido por inicial, generados una vez por
  `build-history.yml` (`scripts/build_history.py`) y servidos por la CDN de Vercel, **sin
  tocar Neon**. El cara a cara los usa (`hist:<liga>` + año) con radar de 8 ejes de
  Understat. Datos que no cambian van en ficheros, no en la base.
- **Transferencia de Neon**: el refresco solo procesa el dataset de Transfermarkt si cambia
  su ETag (caché de Actions), mide los MB de cada paso (`scripts/egress_proxy.py`) y, con
  menos de 600 MB en el mes, se salta los pasos de jugadores.
- **"Errores de cuota"**: estudiados con datos reales y descartados (no dan dinero;
  `scripts/research_odds_value.py`). No vender apuestas de valor.

## Producción (todo gratis)

- API en Vercel, proyecto `el-regista-api` (https://el-regista-api.vercel.app; `index.py`
  en la raíz): desde la raíz `npx vercel deploy --prod --yes`. Con `VERCEL=1` exige clave
  y oculta /docs. Límite de 5 min por función; estado en memoria por instancia.
- Web en Vercel (https://elregista.vercel.app): `cd web && npx vercel --prod --yes`. El
  navegador llama a la API por `/api/*` (rewrite): sin CORS.
- **Trampa**: el `vercel.json` raíz lleva `"git": {"deploymentEnabled": false}`; sin eso
  cada push publicaba la API en elregista.vercel.app. Web y API se despliegan solo por CLI.
- BD en **Neon** Free (Washington iad1, junto a Vercel y los runners de GitHub). Vercel
  enmascara `DATABASE_URL` al hacer `env pull`: lo que necesite la BD se hace desde
  GitHub Actions. Las migraciones NO corren al desplegar: las aplica el refresco.
  **Límite de 5 GB/mes de transferencia** (se agotó en 2 días en oct 2026 y hubo que pasar
  a un proyecto nuevo con `migrate-to-neon.yml`): las lecturas masivas (gemelos,
  explorador, pronósticos) se sirven de memoria 3 h (`presentation/api/read_cache.py`), la
  web cachea 3 h y el e2e contra la API real solo corre si cambia `web/`. Cualquier
  consulta nueva que lea tablas enteras debe ir por `READ_CACHE`.
  El panel `/admin` muestra la transferencia del mes con `NEON_API_KEY` y `NEON_PROJECT_ID`
  (variables del proyecto `el-regista-api`; sin ellas dice "Neon sin conectar").
- Secretos solo como variables de entorno (Vercel / GitHub secrets `DATABASE_URL`,
  `API_BASE_URL`, `INGESTION_API_KEY`); nunca en ficheros del repo ni en el chat. En local
  (`docker compose up`) salen de un Vault en modo desarrollo (`infrastructure/secrets/vault.py`,
  fuente de `pydantic-settings` por debajo de las variables; solo si hay `VAULT_ADDR`). Los
  tests que miran ajustes deben quitar las variables que el CI define (`DATABASE_URL`).
- **DevSecOps** (`security.yml` en cada push; `dast.yml` los lunes): Semgrep e informe de
  Bandit, gitleaks (bloquea), Trivy (bloquea CVE CRITICAL y configuración HIGH), ZAP
  baseline contra el stack de Compose. Falsos positivos marcados en la línea con su motivo
  (`# nosec`, `# nosemgrep`, `# trivy:ignore`, `.gitleaksignore`, `.zap/rules.tsv`); tabla
  de hallazgos en el README. Contenedores sin root (`app` uid 10001, `node`).
- Workflows: `weekly-fbref-refresh.yml` (martes y viernes; también con un push que toque
  `.github/refresh-now`; ingesta con una API local sobre Neon en el runner), `monitor.yml`,
  `backup.yml`, `web-quality.yml`, `ci.yml`.
