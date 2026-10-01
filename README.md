# El Regista

**Scout y pronósticos de fútbol con datos reales.** Una web para descubrir y comparar
jugadores y para saber qué puede pasar en cada partido, con todo el modelo a la vista y
un historial de aciertos que no se puede maquillar.

🌐 **Web:** https://web-seven-tan-39.vercel.app · **API:** https://api-production-5ac3.up.railway.app/docs

Proyecto personal construido con **TDD estricto**, **Clean Architecture** y coste cero:
todas las fuentes de datos, el alojamiento y las herramientas son gratuitos.

---

## Qué hace

### Scout (jugadores)
| Herramienta | Qué ofrece |
|---|---|
| **Buscar jugador** | Ficha completa: rendimiento por 90', percentiles frente a los de su puesto, mapa de tiros, valor de mercado y evolución. |
| **Explorador** | Filtra por liga, edad, posición, precio y minutos, y ordena por cualquier métrica (14 ligas). |
| **Gemelos** | Jugadores con el mismo estilo de juego, ordenados por parecido y por precio. |
| **Comparar** | Cara a cara con radar, percentiles, tiros y veredicto. |
| **En racha** | Los más en forma de las últimas semanas, con imagen lista para compartir. |

### Pronósticos (partidos)
| Herramienta | Qué ofrece |
|---|---|
| **Próximos partidos** | 1X2, marcadores, goles, córners, tarjetas, faltas, tiros y probabilidad de que cada jugador marque o asista. |
| **Historial de aciertos** | Predicciones guardadas antes de cada partido y puntuadas con el resultado real, más la temporada reconstruida sin mirar el futuro. |
| **Equipos** | Clasificación real, por goles esperados (xPts) y estilo (presión, llegadas). |

## Cómo de bien funciona

Todos los modelos se ajustaron en la 24/25 y se validaron en temporadas que no vieron:

- **1X2** (Poisson + Dixon-Coles con fuerzas por xG): Brier 0,594 en la 25/26 frente a
  0,649 de referencia. En la 26/27, 49% de aciertos (el azar da un 33%) y **87% cuando el
  modelo da un 60% o más**.
- **Mercado**: las cuotas de cierre (Brier 0,582) superan al modelo, así que cuando hay
  cuotas la web usa las del mercado como pronóstico principal. Se dice tal cual.
- **Córners, faltas y tiros** (binomial negativa por equipo): mejoran a la media de la liga;
  las amarillas quedan a la par.
- **Goleadores** ("marca si juega"): Brier 0,067 frente a 0,074 en 10.840 pronósticos.

La página [Cómo funciona](https://web-seven-tan-39.vercel.app/como-funciona) explica cada
modelo y sus límites.

## Datos

| Fuente | Qué aporta |
|---|---|
| **FBref** (vía dataset público de Kaggle) | Estadísticas por jugador de las 5 grandes ligas. |
| **Understat** | xG, xA, tiros con coordenadas, alineaciones y calendario. |
| **Transfermarkt** (web y dataset de Kaggle) | Fotos, fechas de nacimiento, posiciones, valores de mercado y 9 ligas más. |
| **football-data.co.uk** | Córners, tarjetas, faltas, árbitros y cuotas por partido. |

Un workflow de GitHub Actions lo actualiza todo los **martes y viernes** y guarda las
predicciones de la semana antes de que se jueguen los partidos.

## Arquitectura

```
web/  Next.js 16 (App Router), Tailwind ─────────► API REST (FastAPI)
                                                     │
src/player_scouting/                                  │
├── domain/          reglas puras: similitud, percentiles, tiros, modelos de predicción
├── application/     casos de uso + puertos (interfaces hacia fuera)
├── infrastructure/  un paquete por fuente (client / mapper / provider) y persistencia
└── presentation/    routers de FastAPI
```

Las dependencias siempre apuntan hacia dentro: el dominio no conoce bases de datos, APIs
ni frameworks. Cada pieza se escribió test primero y el historial lo refleja con commits
en pareja (`test: …` y luego `feat: …`, [Conventional Commits](https://www.conventionalcommits.org/)).

**Stack:** Python 3.14, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, httpx, uv, pytest,
mypy y Ruff · Next.js 16, TypeScript, Tailwind CSS · Railway (API y base de datos),
Vercel (web) y GitHub Actions (datos).

## Identidad visual

La marca está hecha a medida y se genera con código, sin fuentes ni iconos genéricos:

- **Regista Display**, una tipografía propia inspirada en los dorsales clásicos.
- El **logo** (la etiqueta amarilla "EL" + REGISTA) y los **iconos** usan el mismo sistema de trazo.
- Todo sale de `scripts/brand/` (shapely + fontTools) hacia `web/app/fonts/`,
  `web/public/brand/` y `web/app/components/icons.tsx`.
- Paleta de pizarra: `#1F3B2D` pizarra · `#F2EFE6` tiza · `#5FA37A` césped · `#F2C230` tarjeta.
- Fotos con licencia libre; los créditos aparecen al pie de la web.

```bash
cd scripts/brand
uv run --with fonttools --with shapely --with brotli python regista_font.py out
python build_logo.py && uv run --with shapely --with fonttools python build_icons.py
```

## Ejecutar en local

Requisitos: [uv](https://docs.astral.sh/uv/), Node 20 y PostgreSQL (Docker o portable).

```bash
# Base de datos: con Docker…
docker compose up -d db
# …o con el Postgres portable de Windows (puerto 5433)
./scripts/local_postgres_start.ps1

# API
uv sync
export DATABASE_URL="postgresql+psycopg://scouting:scouting@localhost:5433/scouting"
uv run alembic upgrade head
uv run uvicorn player_scouting.presentation.api.main:app --reload

# Web (en otra terminal)
cd web
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

La carga de datos se hace con los endpoints `/ingestion/*` (protegidos con la cabecera
`X-Ingestion-Key` si `INGESTION_API_KEY` está definida). El workflow
`.github/workflows/weekly-fbref-refresh.yml` muestra el orden completo.

## Tests y calidad

```bash
uv run pytest                      # los de Postgres se saltan sin DATABASE_URL
DATABASE_URL=… uv run pytest       # con base de datos
uv run mypy && uv run ruff check .
cd web && npx tsc --noEmit && npm run lint && npm run build
```

Los tests de cada fuente usan respuestas reales recortadas y `httpx.MockTransport`, así que
no necesitan red.

## Estructura

```
├── src/player_scouting/   backend (dominio, aplicación, infraestructura, presentación)
├── tests/                 misma estructura que src/
├── alembic/               migraciones
├── web/                   Next.js: app/ (páginas y componentes), lib/ (cliente de la API)
├── scripts/               Postgres portable, enriquecimiento remoto y marca (scripts/brand)
└── .github/workflows/     CI y actualización de datos
```

## Licencia

Todos los derechos reservados. El repositorio es público como muestra de trabajo
personal; no se concede permiso para copiar, modificar o reutilizar el código sin
autorización expresa del autor. Los datos pertenecen a sus fuentes y las fotos a sus
autores, según sus licencias.
