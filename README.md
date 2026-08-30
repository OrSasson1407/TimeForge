# TimeForge

**Constraint-based school timetabling and dynamic rescheduling system.**

TimeForge generates, validates, optimizes, and dynamically reschedules school timetables. It guarantees zero hard-constraint violations (no teacher/class/room double-booking, no room-capability mismatches, ...), optimizes for teacher/class preferences and schedule quality, explains every automatic decision, and — when a real-world disruption occurs (a teacher becomes unavailable, a room closes) — repairs the existing published schedule with minimal disruption instead of regenerating it from scratch.

This is a Software Engineering final project. The complexity is intentionally concentrated in the scheduling domain (constraint satisfaction, heuristic search, local-search optimization, disruption-minimizing repair) rather than in infrastructure.

## Problem & Product

See [docs/02-PRD.md](docs/02-PRD.md) for the full product requirements. In short: schools must assign lessons (class × subject) to teachers, rooms, and time periods without conflicts, while satisfying availability and capability constraints, and while optimizing preferences. TimeForge is the system of record for that timetable across its entire lifecycle — draft, published, and every subsequent revision.

## Architecture

Modular monolith: React/TypeScript frontend → FastAPI backend (API → Application → Domain → Infrastructure layers) → Firebase Firestore. The scheduling engine is pure Python with **no** dependency on FastAPI or Firebase, so it is independently testable and explainable. See [docs/03-ARCHITECTURE.md](docs/03-ARCHITECTURE.md) for the full diagrammed architecture and [docs/04-DESIGN.md](docs/04-DESIGN.md) for the algorithm design (backtracking CSP + simulated annealing, and the disruption-minimizing rescheduling engine).

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| Backend | Python + FastAPI + Pydantic |
| Database | Firebase Firestore (sole persistent store) |
| Auth | Firebase Authentication |
| Backend tests | pytest |
| Frontend tests | Vitest + React Testing Library |
| E2E tests | Playwright |
| Backend quality | Ruff, pyright |
| Frontend quality | ESLint, Prettier, tsc |

Full rationale in [docs/06-TECH_STACK.md](docs/06-TECH_STACK.md).

## Documentation

The seven foundation documents in [docs/](docs/) are the project's source of truth — read them before making changes:

1. [01-CLAUDE.md](docs/01-CLAUDE.md) — instructions and rules for working on this codebase
2. [02-PRD.md](docs/02-PRD.md) — product requirements
3. [03-ARCHITECTURE.md](docs/03-ARCHITECTURE.md) — architecture
4. [04-DESIGN.md](docs/04-DESIGN.md) — domain model, algorithms, design
5. [05-DATABASE.md](docs/05-DATABASE.md) — Firestore data design
6. [06-TECH_STACK.md](docs/06-TECH_STACK.md) — technology decisions
7. [07-CODE_STANDARDS.md](docs/07-CODE_STANDARDS.md) — coding standards

## Repository Layout

```text
TimeForge/
├── docs/            # the seven foundation documents
├── backend/         # FastAPI app, domain model, scheduling engine
├── frontend/        # React + TypeScript + Vite app
├── tests/e2e/       # Playwright end-to-end tests
├── firebase.json, firestore.rules, firestore.indexes.json, .firebaserc
├── .env.example
└── .gitignore
```

## Local Development Setup

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js LTS, and (for Firestore/Auth emulation) the [Firebase CLI](https://firebase.google.com/docs/cli).

```bash
cp .env.example .env   # fill in real values as needed; never commit .env
```

### Firebase emulators (Firestore + Auth)

```bash
firebase emulators:start --only firestore,auth
```

Unit and integration tests do not require live production Firebase credentials — they run against this emulator or against in-memory fakes.

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload   # http://localhost:8000
```

Backend tests, lint, type-check:

```bash
uv run pytest
uv run ruff check .
uv run pyright
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Frontend tests, lint, format, type-check:

```bash
npm run test
npm run lint
npm run format:check
npm run typecheck
```

### End-to-end tests

Playwright starts both dev servers itself (`tests/e2e/playwright.config.ts`); the frontend one needs `frontend/.env` configured first (see `frontend/README.md` — without it, the app fails to load at all, so every E2E test would time out waiting for the page). Scope is intentionally limited to what's testable without a live Firebase project — login/validation, not deeper authenticated flows (docs/07-CODE_STANDARDS.md §22).

```bash
cd tests/e2e
npm install
npx playwright install chromium
npm run test
```

## Project Status

Complete through Phase 10 (Quality) — all ten phases of the implementation phase order in [docs/01-CLAUDE.md](docs/01-CLAUDE.md) §"Agent Workflow" (Domain → Constraints → Scheduling Engine → Optimization → Firebase → API → Frontend → Rescheduling → Quality):

- **Domain model** (Phase 2): School, Teacher, Class, Subject, Room, LessonRequirement/Lesson, Availability, Schedule/ScheduleVersion/ScheduleAssignment, User, AuditEvent — pure, framework-free dataclasses.
- **Constraint engine** (Phase 3): HC-001..HC-009 (hard) and SC-001..SC-010 (soft) as independent strategy classes behind one `ConstraintEvaluator`.
- **Scheduling engine** (Phase 4): backtracking CSP search with forward checking and dynamic MRV/degree/LCV heuristics; benchmarked against Small/Medium/Large synthetic scenarios (real, measured numbers in [docs/03-ARCHITECTURE.md](docs/03-ARCHITECTURE.md) §30).
- **Optimization** (Phase 5): simulated-annealing local search over the soft constraints, with an explainable 0–100 quality score.
- **Firebase persistence** (Phase 6): Firestore-backed repositories for every entity, Firebase Auth ID token verification, Firestore security rules and composite indexes. Validated at the time via thorough tests against in-memory fakes (that environment's JDK 17 was below the emulator's JDK 21+ requirement); runtime-verified against a real, live emulator in Phase 10 — see `backend/README.md` and the Phase 10 bullet below.
- **API layer** (Phase 7): FastAPI routers for every resource (schools, catalog entities, availability, constraint configuration, the full generate → validate-move → apply-move → publish → compare scheduling workflow, audit log, `/auth/me`), application-layer use cases, a single `DomainError` → JSON error-envelope exception handler, and an API test suite exercising all of the above through `TestClient` against the same in-memory fakes.
- **Frontend** (Phase 8): a React/TypeScript SPA wired to every Phase 7 endpoint — Firebase Auth sign-in with role-gated routing, a generic admin CRUD screen (Management) reused across all seven catalog entities, availability grids (teacher self-service + admin), a constraint-weight configuration screen, and the full scheduling workspace (generate, version list/publish, a class/teacher/room timetable grid, propose-validate-apply manual moves, version comparison), plus an audit log viewer. Server state goes through TanStack Query, auth state through a single React Context — no general client-state store (see [docs/07-CODE_STANDARDS.md](docs/07-CODE_STANDARDS.md) §9 "Frontend State" for the rationale). Verified with a component/unit test suite (Vitest + React Testing Library) and a manual walkthrough against the real backend in a browser.
- **Rescheduling** (Phase 9): `ReschedulingEngine` ("freeze unaffected, repair the rest") reuses the exact same backtracking search and simulated-annealing optimizer the full-generation `Solver` uses (docs/01-CLAUDE.md rule 8 — one implementation of search, not two), seeded with the frozen unaffected assignments and a lesson domain restricted to whatever a disruption actually invalidated. Implements `TEACHER_UNAVAILABLE`/`ROOM_UNAVAILABLE` (the two demonstrated in the PRD's acceptance criteria); the other three `ReschedulingEventType` values are recognized but not yet handled, and the engine says so explicitly rather than mishandling them. Reports a measured `DisruptionCost` (moved assignments, changed rooms/teachers, soft-penalty delta) alongside the new Draft version. Full workflow (`POST /schedules/reschedule`, `GET /schedules/rescheduling-events`) and a frontend panel to report a disruption and see the repair/UNREPAIRABLE outcome, plus a disruption history view.
- **Quality** (Phase 10): a project-wide correctness/robustness pass rather than new features.
  - A shared invariant/property-test helper (`tests/support/invariants.py`, docs/02-PRD.md §17/§35) is now run against every generated **and** rescheduled result, at realistic scale — including, for the first time, a Large (50-class, ~1150-lesson) scenario and a full-scale rescheduling repair, not just the small hand-built problems used for unit tests.
  - That realistic-scale rescheduling test caught a real bug: the simulated-annealing optimizer had no concept of "frozen" assignments during a repair, so a disruption-minimization *penalty* (probabilistic, not a guarantee) was the only thing stopping it from relocating an assignment nobody asked to touch. Fixed by having the optimizer's neighbor moves respect an explicit frozen-lesson set.
  - A second bug, also found via this pass: `app.domain.constraints` and `app.domain.scheduling` have a genuine two-way relationship (constraints type-hint scheduling's value objects; scheduling constructs concrete constraint instances), and importing one before the other could crash with a circular-import error depending on which happened first — a real, import-order-dependent bug, not a test artifact. Fixed with the standard `TYPE_CHECKING`-guarded-import pattern across the constraint modules; documented in docs/07-CODE_STANDARDS.md §7 so it isn't reintroduced.
  - `scripts/seed.py`: a real seed-data script for a demo school (reuses the "Small" benchmark scenario plus proper `Subject` catalog entities, and provisions a working demo Administrator account), refusing to run without an emulator host configured.
  - The Phase 6 live-verification gap was closed for real: installed JDK 21, ran the actual Firebase Emulator Suite (Firestore + Auth), and exercised every Firestore/Auth repository through `scripts/seed.py` plus a full live `generate → publish → reschedule` workflow driven by real HTTP requests against the FastAPI server, authenticated with a real Auth-emulator-issued ID token. This surfaced and fixed a third bug: `credentials.ApplicationDefault()` (the Firebase Admin Python SDK) still requires discoverable Google Application Default Credentials even when every read/write targets a local emulator — fixed with an in-memory throwaway service-account credential auto-selected whenever emulator env vars are set (see `backend/app/infrastructure/firebase/client.py`). Every touched repository's module docstring now says "Runtime-verified in Phase 10" instead of "NOT runtime-verified."
  - A working Playwright E2E suite (previously scaffolded but not runnable in this environment — `uv` isn't on PATH here, which the config now falls back around) covering what's testable without a live Firebase project: the login gate, form validation, and invalid-credential error handling.
  - Two stale cross-references to a PRD section that never existed (`§40`, in `05-DATABASE.md`/`07-CODE_STANDARDS.md`) corrected to point at the actual invariants (§17).
