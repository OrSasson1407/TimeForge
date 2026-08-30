# 06-TECH_STACK.md — Technology Decision Document

## 1. Technology Overview

TimeForge is a modular-monolith web application: a React/TypeScript SPA talking to a Python/FastAPI REST backend, with Firebase Firestore as the sole persistent store and Firebase Authentication for identity. No ML/AI libraries, no additional databases, no distributed infrastructure.

## 2. Frontend

**React + TypeScript + Vite.**

- *Why:* React's component model fits the app's structure (timetable grid, management CRUD screens, dashboards) well; TypeScript gives compile-time safety for the many typed entities (Teacher, Class, Assignment, …) mirrored from backend Pydantic models; Vite gives fast dev-server startup/HMR, important for iterative UI work on a data-dense timetable grid.
- *Advantages:* huge ecosystem, strong typing story with TS, fast local iteration with Vite.
- *Disadvantages:* SPA requires deliberate routing/auth-state handling; React's flexibility means state-management discipline must be self-imposed (addressed in [07-CODE_STANDARDS.md](07-CODE_STANDARDS.md) §9 "Frontend State").
- *Alternatives considered:* Vue (rejected — smaller ecosystem for the specific data-grid/drag-drop components likely needed; no strong reason to deviate from the more common React choice for this stack); Angular (rejected — heavier framework overhead not justified for this app's scope); plain server-rendered templates (rejected — the interactive timetable/drag-and-drop and async generation-progress UX genuinely need a client-side app).
- *Phase 8 additions:* `react-router-dom` (declarative routing + auth/role route guards) and `@tanstack/react-query` (server-state caching/fetching for every API resource). *Decision:* these are the two justified exceptions to [01-CLAUDE.md](01-CLAUDE.md) rule 11 ("do not add a state-management library merely because it is popular") — React Query specifically replaces what rule 11 itself asks for ("a small dedicated data-fetching layer"), not a general client-state store, and routing is a structural requirement (multiple role-gated screens) rather than a state-management choice. No Redux/Zustand/Jotai/etc. was added: the only cross-cutting client state is auth identity/role, handled by a single React Context (`state/AuthContext.tsx`).

## 3. Backend

**Python + FastAPI + Pydantic.**

- *Why:* FastAPI gives typed request/response models via Pydantic (matching the strict validation needs of scheduling input), automatic OpenAPI docs, and async support for long-running generation/rescheduling jobs. Python is well suited to the algorithm-heavy scheduling engine (clear, readable implementation of CSP/backtracking/local-search — important for an academically explainable, testable engine) while FastAPI keeps the web layer thin.
- *Advantages:* fast to build correct, validated APIs; Pydantic models double as the domain's serialization boundary; large ecosystem for testing (pytest) and quality (Ruff).
- *Disadvantages:* Python's raw computational speed is lower than a compiled language for the solver's inner loop; mitigated by algorithmic efficiency (heuristics, incremental scoring — [04-DESIGN.md](04-DESIGN.md) §29) rather than raw throughput, which is appropriate at the project's target scale (§30 of Architecture doc).
- *Alternatives considered:* Node/Express+TS (rejected — would require a second language for the algorithm-heavy engine, or force awkward JS-side CSP code; Python's clarity for algorithmic code was preferred for an academically explainable engine); Java/Spring (rejected — significantly more ceremony for a project of this scope, no compensating benefit here); Go (rejected — faster, but weaker ecosystem fit for rapid Pydantic-style validated APIs and less idiomatic for expressing the backtracking/annealing algorithms clearly for review).

## 4. Scheduling Engine

**Pure Python, framework-free** (`backend/app/domain/scheduling`).

- *Why:* Must have zero dependency on FastAPI/Firebase to remain independently testable and swappable (Architecture Rule 1–2). Implemented as plain Python classes/functions operating on domain objects — see [04-DESIGN.md](04-DESIGN.md) §9–17 for the algorithm.
- No external solver library (e.g., OR-Tools) is used — see [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §37 for the explicit rationale (academic explainability of a hand-built algorithm is a project goal, not just a means to an end).

## 5. Database

**Firebase Firestore — the sole persistent database.**

- *Why:* Serverless, managed NoSQL fits the document-oriented, per-version-snapshot schedule design ([05-DATABASE.md](05-DATABASE.md)); integrates directly with Firebase Authentication for a coherent identity+data story; free/generous local emulator supports credential-free testing (NFR-008).
- *Advantages:* no infrastructure to operate; native support for the transactions/batched writes the domain needs ([04-DESIGN.md](04-DESIGN.md) §30–31); scales automatically for this project's realistic load.
- *Disadvantages:* no server-side joins or ad hoc relational queries — addressed by the denormalization/reference strategy in [05-DATABASE.md](05-DATABASE.md) §6–7; eventual consistency nuances on some query types — mitigated by using transactions exactly where strict consistency is required (§11 of that document).
- *Alternatives explicitly rejected per project mandate:* PostgreSQL, MySQL, MongoDB, SQLite (production), Supabase, DynamoDB, Redis-as-persistent-store. No exception is made anywhere in the design.

## 6. Authentication

**Firebase Authentication.**

- *Why:* Pairs naturally with Firestore, provides email/password (and extensible OAuth) sign-in out of the box, and issues verifiable ID tokens the backend checks via the Firebase Admin SDK — no custom auth/session infrastructure to build or secure.
- *Alternatives considered:* Custom JWT auth (rejected — reinvents what Firebase Auth already provides safely, no benefit here); Auth0/other IdP (rejected — adds a second vendor relationship with no functional gain over the already-mandated Firebase project).

## 7. Testing

- **pytest** (backend unit/integration/API tests) — the de facto standard for Python, rich fixture support for building `SchedulingProblem` test scenarios.
- **Vitest + React Testing Library** (frontend unit/component tests) — Vitest integrates natively with Vite's config/transform pipeline (faster, less config duplication than Jest in a Vite project); RTL encourages testing user-visible behavior over implementation detail, appropriate for the timetable UI's interaction-heavy components.
- **Playwright** (E2E) — reliable cross-browser automation, good support for the async/progress-reporting flows (generation, rescheduling) that a simpler tool might struggle to wait on correctly.

## 8. Build Tools

Vite (frontend bundling/dev server). Backend needs no bundler; FastAPI/Uvicorn serves directly from source in development.

## 9. Code Quality

- **Ruff** (Python) — combines linting and formatting in one fast tool, replacing the need for separate flake8/isort/black configuration.
- **ESLint + Prettier** (TypeScript/React) — ESLint for correctness/style rules (including React hooks rules), Prettier for consistent formatting, the standard pairing for this ecosystem.
- **mypy** (or **pyright**) for Python static typing — *Decision:* use **pyright** (via `pyright` CLI or the `basedpyright` package) for its speed and strong inference, consistent with FastAPI/Pydantic's typing-first idioms; documented here as the chosen tool so CI/editor config stays consistent. TypeScript's own compiler (`tsc --noEmit`) handles frontend type checking in strict mode.

## 10. API

REST via FastAPI, with OpenAPI schema auto-generated from the Pydantic models (useful both for documentation and for generating the frontend's typed API client surface by hand-authored mirrors in `frontend/src/types`, kept in sync manually per [01-CLAUDE.md](01-CLAUDE.md) rule 11 — no codegen tool is introduced without a documented need).

## 11. Deployment

Documented conceptually in [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §34; not built until MVP functionality is complete (per the "no implementation yet" gate on the foundation documents). Target: single containerized FastAPI service + static-hosted frontend build, both against one Firebase project. No Kubernetes/orchestration layer — unjustified at this project's scale (master prompt §30).

## 12. Development Environment

- Backend: a modern Python version (3.12+) managed per-project (see §13).
- Frontend: Node.js LTS + npm (per master-prompt mandate to use npm for the frontend).
- Firebase: local Emulator Suite for Firestore + Authentication (§15).

## 13. Dependency Management

**Backend: `uv`** (Astral's Python package/dependency manager).

- *Why:* single fast tool for virtual environments, dependency resolution, and lockfiles (`uv.lock`); significantly faster than Poetry for install/resolve; increasingly the modern default in the Python ecosystem; integrates cleanly with Ruff/pyright/pytest without extra plugin glue.
- *Alternatives considered:* Poetry (rejected — slower dependency resolution, more configuration surface for no added benefit here); plain `pip` + `requirements.txt` (rejected — no lockfile/reproducibility guarantees, weaker dependency-graph resolution).

**Frontend: `npm`** per explicit project mandate.

## 14. Environment Variables

Required variables are documented in `.env.example` (created during Phase 1 implementation, not in this document) covering: Firebase project config (frontend, public), Firebase service account path (backend, local-dev only — never committed), API base URL, solver defaults (timeout, seed) if overridable per environment. Secrets are never hardcoded or committed ([01-CLAUDE.md](01-CLAUDE.md) §9).

## 15. Local Development

Firebase Emulator Suite (Firestore + Authentication) runs locally so that:
- Unit/integration tests never require live production credentials (NFR-008).
- Developers can reset to a clean state between test runs.
- Seed data (PRD §"Seed Data" / master prompt §42) is loaded into the emulator via a documented script (`scripts/seed.py`), never into production by accident (the script refuses to run without an explicit emulator-host environment variable set).

**Requires JDK 21+.** The `firebase-tools` emulators run on a bundled JVM and refuse to start on Java below 21. This was first discovered in Phase 6, whose development environment (JDK 17 only) could not start the emulator — the Firestore/auth repository implementations (`app/infrastructure/repositories/`) were written and type-checked (`pyright` validates every call against the real `google-cloud-firestore` type stubs) but were not exercised against a live emulator at that point; contract-level behavior was instead verified against in-memory fakes (`backend/tests/support/fakes.py`), the explicitly sanctioned alternative (docs/07-CODE_STANDARDS.md §22, this section). Phase 10 installed a JDK 21 and ran `firebase emulators:start --only firestore,auth` for real, exercising every Firestore/Auth repository through `scripts/seed.py` and a full live generate → publish → reschedule HTTP workflow (see `backend/app/infrastructure/repositories/generic_firestore.py`'s module docstring for what was covered). The in-memory fakes remain the default for day-to-day test runs; run the emulator locally (JDK 21+) when you need to verify the real Firestore-specific implementations.

## 16. CI/CD

*Decision:* a CI pipeline (lint + type-check + unit/integration tests for both frontend and backend, against the Firebase Emulator) is planned as part of Phase 10 (Quality) of implementation, not built during the foundation-documentation phase. Documented here so the expectation is explicit: every PR must pass lint, type-check, and test stages before merge once CI exists.

## 17. Monitoring

No external APM/monitoring vendor is introduced for MVP — structured application logs (§18) are sufficient at this project's scale and are the documented, deliberate choice (not a gap) per [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §29.

## 18. Logging

Python's standard `logging` module configured for structured (JSON in production, human-readable in development) output, with correlation/request IDs threaded through the application layer for tracing a single generation/rescheduling run through its log lines (Architecture §28).

## 19. Security Tooling

- `pip-audit` (or `uv`'s built-in advisory checking, when available) for backend dependency vulnerability scanning.
- `npm audit` for frontend dependency scanning.
- Ruff's security-relevant lint rules (e.g., `S`-prefixed bandit-derived rules) enabled.
- No additional SAST/DAST tooling introduced beyond what's justified for a final project; the `security-review` workflow (see [07-CODE_STANDARDS.md](07-CODE_STANDARDS.md) §"Security") is the primary manual gate.
