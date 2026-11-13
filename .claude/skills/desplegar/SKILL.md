---
name: desplegar
description: Publica El Regista (web y API, un solo servicio en Render) tras pasar las comprobaciones. Solo cuando el usuario lo pide con /desplegar.
disable-model-invocation: true
---

# Desplegar

Desde noviembre de 2026 la web y la API van juntas en un servicio gratuito de Render
(`elregista`, https://elregista.onrender.com; `render.yaml` y `deploy/render/`), porque
Vercel Hobby pausó la cuenta (402). Render **no** despliega con cada push
(`autoDeploy: false`): el despliegue lo lanza el usuario con **Manual Deploy → Deploy
latest commit** en dashboard.render.com. Oracle está descartado: no
proponerlo.

## 1. Comprobaciones (parar al primer fallo y contarlo)

- `git status`: sin cambios sin commitear. Si los hay, preguntar antes de seguir.
- API: `uv run pytest`, `uv run mypy`, `uv run ruff check .`
- Web: `cd web && npx tsc --noEmit && npm run lint && npm run build`
- ¿Hay migraciones nuevas en `alembic/versions/` desde el último despliegue? Las
  migraciones **no** corren al desplegar: las aplica el refresco. Si el código nuevo
  necesita columnas nuevas, primero lanzar el refresco (commit que toque
  `.github/refresh-now` y push), esperar a que acabe en verde y después desplegar.

## 2. Desplegar

- `git push` y pedir al usuario que pulse **Manual Deploy → Deploy latest commit** en
  Render (5-10 min). La portada y los rankings se prerenderizan en el build con los datos
  de ese momento: también hay que redesplegar tras restaurar o recargar la base.

## 3. Verificar en producción

- `curl -s https://elregista.onrender.com/api/health` → 200 (dormido tarda ~1 min).
- `curl -s https://elregista.onrender.com/api/overview` → cifras reales (jugadores > 15.000).
- Abrir una página tocada por el cambio con `curl` y comprobar que trae el contenido nuevo.

Contar al usuario qué se publicó, las URLs y el resultado de cada comprobación.
