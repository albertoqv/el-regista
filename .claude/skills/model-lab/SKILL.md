---
name: model-lab
description: Probar o cambiar los modelos de pronóstico (1X2, Dixon-Coles, vidas medias, ascendidos, calibración) con el laboratorio walk-forward cacheado y reanudable. Úsala antes de tocar domain/prediction.py, domain/counts.py o cualquier parámetro de un modelo, y cuando haya que comparar variantes con el backtest.
---

# Laboratorio de modelos

Un cambio en un modelo solo se publica si mejora en una temporada que no ha visto.
Este laboratorio lo mide sin repetir trabajo: los datos viven en su propia base de
datos y cada variante se guarda en disco en cuanto se calcula.

## Antes de nada

1. Postgres local en marcha (puerto 5433): `scripts/local_postgres_start.ps1`.
   Si responde "el sistema de base de datos está iniciándose", espera unos segundos.
2. Los datos están en la base **`scouting_lab`**, no en `scouting`: los tests de
   persistencia vacían `scouting`, así que nunca guardes ahí datos de experimentos.
   **No vacíes ni borres `scouting_lab`.**
3. `uv run python scripts/model_lab.py prepare` solo hace falta si `scouting_lab` está
   vacía o para refrescar la temporada en curso. No vuelve a descargar las temporadas que
   ya tiene.

## Ejecutar

- Rápido (todo lo cacheado está ya calculado): `uv run python scripts/model_lab.py run all`.
- Largo (variantes nuevas, varios minutos cada una): **siempre en segundo plano**, con
  `scripts/model_lab_background.ps1 [experimentos]`. Es un proceso aparte: sigue aunque se
  cierre la terminal o la sesión de Claude. Si se corta, vuelve a lanzarlo: retoma desde
  `.cache/model_lab/` y no recalcula lo terminado.
- Progreso en `.cache/model_lab/run.log`; resultados en `.cache/model_lab/results.json`
  (`model_lab.py report`).
- Para esperar el final desde Claude: un `until grep -q '"promoted"' .cache/model_lab/results.json`
  en segundo plano, no bucles de `sleep`.

## Añadir un experimento

En `run()` de `scripts/model_lab.py`: una variante = `lab.rows("<nombre-único>", ratings)`,
con `ratings(matches, day, league, fixture) -> LeagueRatings`. El nombre forma parte de la
clave de caché: si cambias la lógica de una variante, cámbiale el nombre. Lo barato
(empates, calibración) se calcula sobre las filas de `base` sin recomputar fuerzas.

## Regla para publicar

- Se ajusta en 24/25 (`"2024"`), se valida en 25/26 (`"2025"`), cada partido solo con
  partidos anteriores.
- `ships: true` solo si mejora las dos temporadas **y** el bootstrap emparejado de 25/26 da
  `p_better >= 0.95`. Por debajo es ruido: no se cambia el modelo y se anota en CLAUDE.md
  qué se probó.
- Si se publica: TDD como siempre (`test:` y luego `feat:`), con el parámetro nuevo en
  `domain/` y su valor documentado junto a la constante.

## Ya probado (no repetir sin una idea nueva)

- Descanso entre partidos: solo vemos liga, no copas; sobreajusta.
- Vida media 60-240 días: mejora como mucho 0,001, ruido.
- Empate (rho) por liga: sobreajusta (25/26 empeora). Rho global y calibración por potencia: ruido.
- Ventaja de campo por liga: ya existe (cada liga tiene sus medias de local y visitante).
