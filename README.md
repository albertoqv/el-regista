# ⚽ Player Scouting & Comparison Tool

> Herramienta de comparación y scouting de jugadores de fútbol, construida como
> ejercicio deliberado de **TDD**, **Domain-Driven Design** y **Clean Architecture**.

## 🎯 Motivación

Este proyecto nace de la intersección entre dos intereses: el fútbol y la
ingeniería del software. En lugar de otro CRUD de práctica, el objetivo es
resolver un problema real: comparar jugadores y encontrar similitudes entre
ellos a partir de sus estadísticas, aplicando el mismo rigor de diseño y
testing que se exige en un equipo de desarrollo profesional: cada pieza
del dominio, desde la más pequeña, ha sido construida test primero.

## 🏗️ Arquitectura

El proyecto sigue **Clean Architecture**: el dominio no depende de nada
externo (ni de una base de datos, ni de una API, ni de un framework web).
Las dependencias siempre apuntan hacia dentro.

```
┌─────────────────────────────────────────────┐
│  Presentación   (API REST con FastAPI)       │  ← ✅ construido
├─────────────────────────────────────────────┤
│  Infraestructura (StatsBomb, Wikidata, BD)   │  ← ✅ construido
├─────────────────────────────────────────────┤
│  Aplicación     (casos de uso)               │  ← ✅ construido
├─────────────────────────────────────────────┤
│  Dominio        (entidades, reglas, servicios)│ ← ✅ construido
└─────────────────────────────────────────────┘
```

*(pendiente: un dashboard web que consuma esta API)*

### El dominio, pieza a pieza

- **`SimilarityScore`** (Value Object): un porcentaje entero de 0 a
  100 que representa cuán parecidos son dos jugadores. Se valida a sí
  mismo: rechaza valores no enteros (incluidos booleanos) y fuera de rango.
- **`Statistics`** (Value Object): agrupa las estadísticas de un
  jugador (por ahora, goles y asistencias), en vez de pasar números
  sueltos por el sistema. Se valida a sí mismo: enteros no negativos.
- **`Player`** (Entidad): su identidad es el `player_id` de StatsBomb,
  no sus datos: dos jugadores con el mismo `player_id` son "el mismo
  jugador" aunque cambien de nombre o de equipo. Valida que el
  `player_id` sea un entero positivo y que la fecha de nacimiento no sea
  futura.
- **`Comparison`** (Value Object): compone dos `Player` y una
  `SimilarityScore`. Es **simétrica**: comparar A con B es lo mismo
  que comparar B con A, si la puntuación coincide.
- **`SimilarityCalculator`** (Servicio de dominio): calcula la
  similitud real entre dos jugadores a partir de sus `Statistics`.
  Por cada métrica (goles, asistencias) usa la fórmula
  `1 - |a-b| / max(a,b)` (con el caso especial de valores iguales →
  similitud 1, evitando así la división por cero), y combina las
  métricas con una media simple para producir una `SimilarityScore`
  final.

### La aplicación: casos de uso

- **`ComparePlayersUseCase`**: obtiene dos jugadores del repositorio y
  delega en `SimilarityCalculator` para compararlos.
- **`FindSimilarPlayersUseCase`**: compara un jugador contra todos los
  demás del repositorio y devuelve el top N ordenado por similitud.
- **`IngestCompetitionUseCase`**: obtiene estadísticas agregadas de una
  competición (vía el puerto `CompetitionStatisticsProvider`),
  resuelve la fecha de nacimiento de cada jugador (vía el puerto
  `BirthDateProvider`) y persiste a los jugadores resueltos. Los
  jugadores sin fecha de nacimiento fiable se omiten y se reportan en
  el resultado, sin abortar el resto de la ingesta.

La aplicación solo depende de sus propios puertos (`PlayerRepository`,
`BirthDateProvider`, `CompetitionStatisticsProvider`), nunca de
infraestructura concreta: las dependencias siguen apuntando hacia
dentro.

### La infraestructura

- **StatsBomb Open Data**: `StatsBombClient` consume por HTTP en
  tiempo real los ficheros públicos de `matches`, `lineups` y `events`.
  `mapper.py` traduce esos eventos a goles/asistencias por jugador
  (gol = evento `Shot` con resultado `Goal`; asistencia = evento `Pass`
  con `goal_assist`), y `StatsBombCompetitionStatisticsProvider` agrega
  esas estadísticas a lo largo de todos los partidos de una competición.
- **Wikidata**: `WikidataBirthDateProvider` resuelve la fecha de
  nacimiento de cada jugador (StatsBomb no la incluye) mediante una
  consulta SPARQL pública, filtrando por humano + ocupación futbolista
  y desambiguando por nacionalidad cuando hace falta.
- **PostgreSQL**: `SqlAlchemyPlayerRepository` persiste jugadores y sus
  estadísticas agregadas; el esquema se gestiona con Alembic.

### La presentación: API con FastAPI

- `GET /players/{player_id}` — datos y estadísticas de un jugador.
- `GET /players/{id1}/compare/{id2}` — compara dos jugadores.
- `GET /players/{player_id}/similar?top=5` — jugadores más parecidos.
- `POST /ingestion/statsbomb/{competition_id}/{season_id}` — ingesta
  una competición completa de StatsBomb Open Data.

## 🧪 Metodología

Cada pieza de lógica de negocio se ha escrito con **TDD** (red → green →
refactor): primero el test que falla, después el código mínimo que lo
hace pasar. El historial de commits del proyecto refleja ese ciclo,
separando explícitamente el commit del test (`test:`) del de su
implementación (`feat:`), siguiendo el convenio de
[Conventional Commits](https://www.conventionalcommits.org/).

## 📦 Stack tecnológico

- **Python 3.14**, con type hints en todas las capas
- **pytest**: testing, incluyendo `pytest.raises` para validar
  excepciones y `pytest.approx` para comparar resultados decimales
- **Ruff**: linter y formatter
- **mypy**: comprobación estática de tipos
- **uv**: gestión de dependencias y de entornos virtuales
- **FastAPI** + **uvicorn**: API REST
- **httpx**: cliente HTTP (StatsBomb Open Data y Wikidata), mockeado
  con `httpx.MockTransport` en los tests
- **SQLAlchemy** + **Alembic**: persistencia y migraciones sobre
  **PostgreSQL**
- **Docker Compose**: entorno de desarrollo local (Postgres + API)
- *(próximamente)* un dashboard (Next.js) que consuma esta API

## 🚦 Estado actual

🟢 Backend funcional de principio a fin, con TDD en todas las capas:

- [x] Dominio: `Player`, `Statistics`, `SimilarityScore`, `Comparison`,
      `SimilarityCalculator`, jerarquía de excepciones propia
- [x] Aplicación: `ComparePlayersUseCase`, `FindSimilarPlayersUseCase`,
      `IngestCompetitionUseCase`, con puertos hacia la infraestructura
- [x] Infraestructura: adaptador de StatsBomb Open Data (HTTP en
      tiempo real), enriquecimiento de fecha de nacimiento vía
      Wikidata, persistencia en PostgreSQL con SQLAlchemy + Alembic
- [x] Presentación: API REST con FastAPI (jugadores, comparación,
      similares, ingesta)
- [x] Docker Compose para desarrollo local, Postgres + Ruff + mypy en CI
- [ ] Dashboard (Next.js)

## ⚙️ Cómo ejecutar el proyecto

Este proyecto usa [uv](https://docs.astral.sh/uv/) para gestionar
dependencias y el entorno virtual, y Docker Compose para levantar
PostgreSQL en local:

```bash
uv sync
cp .env.example .env          # ajusta DATABASE_URL si hace falta
docker compose up -d db       # levanta Postgres
uv run alembic upgrade head   # aplica las migraciones
uv run uvicorn player_scouting.presentation.api.main:app --reload
```

Con la API arriba, puedes ingerir una competición real de StatsBomb
Open Data (por ejemplo, el Mundial 2018: `competition_id=43`,
`season_id=3`) y consultar los datos ingeridos:

```bash
curl -X POST http://localhost:8000/ingestion/statsbomb/43/3
curl http://localhost:8000/players/{player_id}
curl http://localhost:8000/players/{id1}/compare/{id2}
curl "http://localhost:8000/players/{player_id}/similar?top=5"
```

También puedes levantar toda la pila (Postgres + API) con
`docker compose up`.

## 🧪 Cómo ejecutar los tests

```bash
uv run pytest
```

Los tests de infraestructura (StatsBomb, Wikidata) mockean el HTTP con
`httpx.MockTransport`, así que no requieren red. Los tests del
repositorio de PostgreSQL se saltan automáticamente si no hay
`DATABASE_URL` definida; para ejecutarlos:

```bash
docker compose up -d db
DATABASE_URL=postgresql+psycopg://scouting:scouting@localhost:5432/scouting uv run pytest
```

## 🧹 Linting, formatting y tipos

```bash
uv run ruff check .
uv run ruff format .
uv run mypy
```

## 📁 Estructura del proyecto

```
player-scouting/
├── alembic/                             # migraciones de base de datos
├── src/
│   └── player_scouting/
│       ├── domain/                      # entidades y reglas de negocio
│       ├── application/
│       │   ├── ports.py                 # interfaces hacia infraestructura
│       │   └── use_cases/                # ComparePlayers, FindSimilarPlayers, IngestCompetition
│       ├── infrastructure/
│       │   ├── statsbomb/                # cliente HTTP + mapper de eventos
│       │   ├── birth_dates/              # WikidataBirthDateProvider
│       │   └── persistence/              # modelos SQLAlchemy + repositorio + settings
│       └── presentation/
│           └── api/                      # FastAPI: schemas, dependencias, routers
├── tests/                                # misma estructura que src/, capa a capa
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
├── pytest.ini
└── README.md
```

## 📄 Licencia

Todos los derechos reservados. Este repositorio es público como
muestra de trabajo personal; no se concede permiso para copiar,
modificar o reutilizar el código sin autorización expresa del autor.
