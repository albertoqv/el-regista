---
name: desplegar
description: Publica la API y/o la web de El Regista en Vercel tras pasar las comprobaciones. Solo cuando el usuario lo pide con /desplegar.
disable-model-invocation: true
---

# Desplegar

Argumento opcional: `api`, `web` o nada (las dos). Ninguno de los dos proyectos se
despliega con un push: el `vercel.json` raíz lleva `"git": {"deploymentEnabled": false}`
a propósito (si no, la API se publicaba en elregista.vercel.app). **No lo quites.**

## 1. Comprobaciones (parar al primer fallo y contarlo)

- `git status`: sin cambios sin commitear. Si los hay, preguntar antes de seguir.
- API: `uv run pytest`, `uv run mypy`, `uv run ruff check .`
- Web: `cd web && npx tsc --noEmit && npm run lint && npm run build`
- ¿Hay migraciones nuevas en `alembic/versions/` desde el último despliegue? Las
  migraciones **no** corren al desplegar: las aplica el refresco. Si el código nuevo
  necesita columnas nuevas, primero lanzar el refresco (commit que toque
  `.github/refresh-now` y push), esperar a que acabe en verde y después desplegar la API.

## 2. Desplegar

- API (desde la raíz): `npx vercel deploy --prod --yes`
- Web: `cd web && npx vercel --prod --yes`

Si se despliegan las dos y la web usa algo nuevo de la API, la API va primero.

## 3. Verificar en producción

- `curl -s https://el-regista-api.vercel.app/health` → 200
- `curl -s https://el-regista-api.vercel.app/health/db` → ms bajos (~2)
- `curl -sI https://elregista.vercel.app/` → 200, y que **no** responda JSON de FastAPI
  (señal de que la API se ha colado en el dominio de la web).
- Abrir una página tocada por el cambio con `curl` y comprobar que trae el contenido nuevo.

Contar al usuario qué se publicó, las URLs y el resultado de cada comprobación.
