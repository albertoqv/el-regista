<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="web/public/brand/logo-dark.svg">
    <img src="web/public/brand/logo-light.svg" alt="El Regista" width="420">
  </picture>
</p>

<p align="center">
  <b>Fútbol con datos de verdad.</b><br>
  Descubre y compara jugadores, y mira qué puede pasar en cada partido.
</p>

<p align="center">
  <a href="https://elregista.vercel.app"><b>elregista.vercel.app</b></a>
</p>

![Portada de El Regista](docs/img/portada.jpg)

---

## Dos productos

### Scout · para los jugadores

| | |
|---|---|
| **Buscar jugador** | La ficha completa de cualquier jugador de 14 ligas: rendimiento por 90 minutos, percentiles frente a los de su puesto, mapa de tiros y valor de mercado. |
| **Explorador** | Filtra por liga, edad, posición, precio y minutos, y ordena por cualquier estadística. Del tipo "delanteros de menos de 15 M€ que marcan". |
| **Gemelos** | El mismo estilo de juego, más barato. Elige un jugador y te salen los que más se le parecen, con su precio. |
| **Comparar** | Dos jugadores cara a cara, con radar, percentiles y veredicto. |
| **En racha** | Quién está en forma en las últimas semanas, con imagen lista para compartir. |

![Ficha de jugador](docs/img/ficha.jpg)

### Pronósticos · para los partidos

| | |
|---|---|
| **Próximos partidos** | Probabilidades de resultado, marcador, goles, córners, tarjetas, faltas y tiros, y quién puede marcar o asistir. |
| **Historial de aciertos** | Lo que dijimos antes de cada partido frente a lo que pasó. Se guarda antes de que empiece y no se puede tocar después. |
| **Equipos** | La clasificación real y la que cada equipo merece por sus ocasiones. |

![Próximos partidos](docs/img/pronosticos.jpg)

## Por qué fiarse

Los números no se esconden:

- **49% de aciertos** en el resultado (1X2) en la temporada 26/27, cuando el azar da un 33%.
- **87% de aciertos** cuando el modelo se moja con un 60% o más.
- Cada predicción se **guarda antes del partido** y se puntúa después: el historial es público.
- Cuando las casas de apuestas aciertan más que el modelo (en el 1X2), la web lo dice y usa sus cuotas.
- La página [Cómo funciona](https://elregista.vercel.app/como-funciona) explica cada cálculo y sus límites.

## Para compartir

Cada jugador y el ranking de En racha tienen su propia imagen, pensada para redes.

<p>
  <img src="docs/img/carta.jpg" alt="Carta de jugador" width="320">
  <img src="docs/img/en-racha.jpg" alt="Ranking En racha" width="320">
  <img src="docs/img/movil.jpg" alt="El Regista en el móvil" width="180">
</p>

## De dónde salen los datos

FBref, Understat, Transfermarkt y football-data.co.uk: estadísticas, goles esperados (xG),
tiros con coordenadas, alineaciones, valores de mercado, córners, tarjetas, árbitros y cuotas.
Todo se actualiza solo **los martes y los viernes**.

## Hecho a mano

Nada genérico: la tipografía (**Regista Display**, inspirada en los dorsales clásicos), el logo
y los iconos están diseñados para El Regista. Las fotos tienen licencia libre y sus autores
aparecen al pie de la web.

---

<details>
<summary><b>Para desarrolladores</b></summary>

### Stack

- **Backend:** Python 3.14, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, httpx y uv.
  Clean Architecture (`domain`, `application`, `infrastructure`, `presentation`) y TDD
  estricto, con commits en pareja `test:` / `feat:`.
- **Web:** Next.js 16 (App Router), TypeScript y Tailwind CSS.
- **Infraestructura gratuita:** Railway (API y base de datos), Vercel (web) y GitHub Actions
  (actualización de datos y CI).
- **API pública:** https://api-production-5ac3.up.railway.app/docs

### Modelos

- Resultado: Poisson + Dixon-Coles con fuerzas por xG, ajustado en la 24/25 y validado en
  la 25/26 (Brier 0,594 frente a 0,649 de referencia; cuotas de cierre 0,582).
- Córners, faltas, tiros y tarjetas: binomial negativa por equipo con encogimiento.
- Jugadores: probabilidad de marcar, asistir o ver tarjeta "si juega", por la probabilidad de
  jugar (Brier 0,067 frente a 0,074 en 10.840 pronósticos).

### Ejecutar en local

```bash
docker compose up -d db              # o ./scripts/local_postgres_start.ps1 (puerto 5433)
uv sync
export DATABASE_URL="postgresql+psycopg://scouting:scouting@localhost:5433/scouting"
uv run alembic upgrade head
uv run uvicorn player_scouting.presentation.api.main:app --reload

cd web && npm install && cp .env.local.example .env.local && npm run dev
```

Los datos se cargan con los endpoints `/ingestion/*` (cabecera `X-Ingestion-Key`). El
workflow `.github/workflows/weekly-fbref-refresh.yml` muestra el orden completo.

### Tests y calidad

```bash
uv run pytest                        # los de Postgres se saltan sin DATABASE_URL
uv run mypy && uv run ruff check .
cd web && npx tsc --noEmit && npm run lint && npm run build
```

### Marca

La tipografía, el logo y los iconos se generan con código en `scripts/brand/` (shapely +
fontTools). Paleta: pizarra `#1F3B2D`, tiza `#F2EFE6`, césped `#5FA37A` y tarjeta `#F2C230`.

</details>

## Licencia

Todos los derechos reservados. El repositorio es público como muestra de trabajo personal; no
se concede permiso para copiar, modificar o reutilizar el código sin autorización expresa del
autor. Los datos pertenecen a sus fuentes y las fotos a sus autores, según sus licencias.
