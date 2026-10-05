---
name: nueva-fuente
description: Añadir una fuente de datos externa nueva (web, CSV, API) a El Regista con el patrón client/mapper/provider, TDD y fixtures reales. Úsala cuando haya que leer datos de un sitio que aún no está en src/player_scouting/infrastructure/.
---

# Nueva fuente de datos

Ejemplos a copiar: `infrastructure/football_data/` (CSV) y `infrastructure/understat/`
(JSON). Sigue el ciclo de la skill `ciclo-tdd`: un par `test:`/`feat:` por paso.

## 0. Antes de escribir código

- **Que sea gratis** y sin cuenta de pago. Lee su robots.txt y sus condiciones y
  cuéntale al usuario lo que dicen antes de seguir (Understat lo prohíbe y el usuario
  aceptó el riesgo; con otra fuente hay que preguntar).
- **Nunca inventes URLs, rutas ni IDs**: descúbrelos haciendo la petición real y
  guarda una respuesta de verdad. Anota en el docstring la URL y el mes en que se verificó.
- Mira si bloquea centros de datos (prueba desde GitHub Actions si hace falta): si es así,
  tendrá que correr desde el PC del usuario como Transfermarkt.
- Apunta la fuente y su licencia en `docs/fuentes-y-licencias.md`.

## 1. Mapper (puro, sin red)

`infrastructure/<fuente>/mapper.py`: texto/JSON → objetos del dominio.
Test con una fixture **pequeña recortada de la respuesta real** (dos o tres filas, incluido
un caso raro: valor vacío, separador de miles, jugador sin minutos...).

## 2. Client (solo HTTP)

`client.py`: recibe un `httpx.Client` en el constructor, construye URLs y devuelve texto o
JSON. Test con `httpx.MockTransport` comprobando la ruta pedida y los casos 404 / 403 / 429.
Bloqueos (403, 429, desafíos de WAF) → `EnrichmentUnavailableError` para que el lote pare
sin marcar nada. Pausas entre peticiones configurables (0 en tests).

## 3. Provider

`provider.py`: une client + mapper y cumple un puerto de `application/ports.py` (créalo si
no existe, como `Protocol`). Test con el client falso.

## 4. Aplicación, persistencia y API

- Caso de uso en `application/use_cases/` probado con los dobles de
  `tests/application/doubles.py`.
- Si hay tablas nuevas: modelo en `persistence/`, migración de Alembic con el siguiente
  número, test de persistencia con `DATABASE_URL`. Si la fuente se cruza con jugadores
  existentes, usa `application/player_matching.py` (nombre + equipo + minutos/goles, nunca
  el primer candidato a ciegas).
- Endpoint `POST /ingestion/<fuente>/...` (exige `X-Ingestion-Key`), registrado en
  `dependencies.py`.
- Paso nuevo en `.github/workflows/weekly-fbref-refresh.yml` con lotes pequeños.

## 5. Cierre

- `uv run pytest && uv run mypy && uv run ruff check .`
- Actualiza "Fuentes de datos" en `CLAUDE.md` y añade una entrada en `docs/historial.md`.
