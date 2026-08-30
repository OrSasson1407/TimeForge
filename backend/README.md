# TimeForge Backend

FastAPI application, domain model, and constraint-based scheduling engine. See [../docs](../docs) for the full specification — this package implements [03-ARCHITECTURE.md](../docs/03-ARCHITECTURE.md) §9 and [04-DESIGN.md](../docs/04-DESIGN.md).

## Setup

```bash
uv sync
```

## Run the API

```bash
uv run uvicorn app.main:app --reload
```

## Test

```bash
uv run pytest              # fast suite (excludes slow scheduling integration tests)
uv run pytest -m slow      # full-scale scheduling integration tests (tens of seconds)
uv run pytest -m ""        # everything
```

## Benchmark the scheduling engine

```bash
uv run python -m scripts.benchmark_scheduling
```

## Firestore repositories

`app/application/repositories/` holds the repository interfaces; `app/infrastructure/repositories/` holds the Firestore-backed implementations. As of Phase 6, these implementations were type-checked (pyright validates every call against the real `google-cloud-firestore` stubs) but had not been run against a live Firestore emulator — that development environment's JDK (17) was below the version `firebase-tools` requires (21+). Contract-level behavior was verified instead against the in-memory fakes in `tests/support/fakes.py`. Phase 10 closed this gap: with a JDK 21 installation, the full emulator suite runs and every Firestore/Auth code path was exercised against it via `scripts/seed.py` plus a real generate → publish → reschedule HTTP workflow (see `app/infrastructure/repositories/generic_firestore.py`'s module docstring for details). The in-memory fakes remain the default for fast unit/integration tests; the emulator is for local verification and CI. To run it yourself:

```bash
firebase emulators:start --only firestore,auth
```

from the repo root, with `FIRESTORE_EMULATOR_HOST` / `FIREBASE_AUTH_EMULATOR_HOST` set per `.env.example`.

## Lint & type-check

```bash
uv run ruff check .
uv run ruff format .
uv run pyright
```
