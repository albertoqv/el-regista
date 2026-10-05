---
name: ciclo-tdd
description: Ciclo TDD de El Regista con el par de commits "test:" y "feat:"/"fix:" en español y mypy + ruff antes de cada commit. Úsala al implementar cualquier funcionalidad o arreglo en el backend Python.
---

# Ciclo TDD

Una funcionalidad = uno o varios pares de commits, uno por capa (dominio, aplicación,
infraestructura, API). Mensajes en español, Conventional Commits, describiendo el
comportamiento, no el código: `test: un partido sin cuotas usa el modelo` →
`feat: un partido sin cuotas usa el modelo`.

## Por cada capa

1. **Rojo.** Escribe el test que describe el comportamiento (nombre en inglés como
   frase: `test_a_blocked_scraper_stops_instead_of_saving_half_a_league`). Ejecútalo y
   comprueba que falla **por la razón esperada** (no por un import roto):
   `uv run pytest ruta/del/test.py -q`
2. **Commit del test** solo con el test (y los cambios mínimos para que compile, p. ej.
   una firma vacía). Antes: `uv run ruff check . && uv run ruff format --check .`
   → `git commit -m "test: <comportamiento>"`
3. **Verde.** El código mínimo que lo hace pasar. Luego refactoriza sin cambiar
   comportamiento.
4. **Antes del segundo commit**, todo esto en verde:
   `uv run pytest -q && uv run mypy && uv run ruff check . && uv run ruff format --check .`
   Si algo falla, se arregla; nunca `--no-verify` ni `# type: ignore` sin motivo escrito.
5. `git commit -m "feat: <mismo comportamiento>"` (o `fix:` / `refactor:`).

## Reglas

- Tests de proveedores con fixtures pequeñas copiadas de respuestas reales y
  `httpx.MockTransport`; nada de red en los tests.
- Si tocas `SqlAlchemyPlayerRepository` o similar, el doble en
  `tests/application/doubles.py` debe comportarse igual.
- **Nunca dependas del reloj real.** Si el código usa `datetime.now`/`date.today`, recíbelo
  como parámetro (`now=`/`today=` en el caso de uso, `_now` en el router) y fíjalo en el
  test: con fechas de prueba cercanas a hoy, el test caduca solo cuando pasa el día.
  Para buscar tests así, ejecuta la suite en otra fecha con `time-machine`
  (`uv run --with time-machine pytest` + un plugin que haga `time_machine.travel(...)`).
- Tests de persistencia: necesitan `DATABASE_URL` (Postgres local, puerto 5433); sin ella
  se saltan, así que si tocas persistencia ejecútalos con la BD encendida. Usan el
  `session` de `tests/infrastructure/persistence/conftest.py` (tablas vacías dentro de una
  transacción que se deshace).
- `except A, B:` sin paréntesis es válido en Python 3.14 (PEP 758).
- No hacer push salvo que el usuario lo pida.
