# 07-CODE_STANDARDS.md — Coding Standards

## 1. General Principles

- Correctness and testability come before cleverness or brevity.
- Every module has one clear responsibility (see layer boundaries in [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §7).
- Prefer small, composable functions/classes over large ones — especially in the constraint engine, where each constraint must stand alone and be independently testable ([01-CLAUDE.md](01-CLAUDE.md) §8, master prompt §16).
- No speculative abstraction: build the interface a component needs today, extend it when a second real need appears.

## 2. SOLID

- **Single Responsibility** — e.g., `TeacherConflictConstraint` checks exactly one hard constraint; `ConstraintEvaluator` only aggregates/queries constraints, never implements one itself.
- **Open/Closed** — new constraints extend the system by implementing `HardConstraint`/`SoftConstraint` (§10, [04-DESIGN.md](04-DESIGN.md)) without modifying the solver core.
- **Liskov Substitution** — any `HardConstraint`/`SoftConstraint`/repository implementation must be substitutable without the caller knowing which concrete type it received (this is what makes fake repositories valid for tests, §"Mocking").
- **Interface Segregation** — repository interfaces expose only the operations their consumers need (e.g., a read-only reporting service doesn't depend on a `save()` method it never calls).
- **Dependency Inversion** — domain/application depend on repository *interfaces*; infrastructure implements them ([03-ARCHITECTURE.md](03-ARCHITECTURE.md) §2, principle 1).

## 3. Clean Code

- Names describe intent, not implementation (`identifyAffectedAssignments`, not `filterStuff`).
- Functions do one thing; if a function needs a "and then" in its description, split it.
- Avoid boolean-flag parameters that change a function's behavior wholesale — prefer separate functions or an enum.
- Guard clauses over deep nesting.

## 4. Naming Conventions

- Domain concepts use the exact terms from [04-DESIGN.md](04-DESIGN.md) §2 everywhere (code, tests, API field names, UI copy) — e.g., always `LessonRequirement`, never `LessonNeed`/`ClassRequirement` as a synonym. Consistent terminology is mandatory across all seven documents and the codebase.
- IDs referenced across documents (`FR-xxx`, `NFR-xxx`, `BR-xxx`, `HC-xxx`, `SC-xxx`) appear verbatim in code comments/tests where a specific requirement/constraint is implemented, to preserve traceability ([02-PRD.md](02-PRD.md) §"Requirement Traceability" pattern).

## 5. File Naming

- Python: `snake_case.py`, test files mirror the module under test as `test_<module>.py`.
- TypeScript/React: `PascalCase.tsx` for components, `camelCase.ts` for hooks/utilities/services, `useX.ts` for hooks.

## 6. Folder Structure

See [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §8–9 for the authoritative backend/frontend layouts. Do not introduce new top-level folders without updating that document.

## 7. Python Conventions

- Type hints on every function signature (parameters and return type); `from __future__ import annotations` where useful for forward references.
- Domain entities as `@dataclass(frozen=True)` where immutability is meaningful (e.g., `CandidateAssignment`, `Score`), regular classes where mutable state is intrinsic (e.g., `ScheduleState` builder during search).
- No bare `except:`; catch specific exceptions and re-raise as a domain error type where appropriate ([04-DESIGN.md](04-DESIGN.md) §24).
- Prefer composition over inheritance for constraint implementations (each implements the `HardConstraint`/`SoftConstraint` protocol; no deep class hierarchies).
- `app.domain.constraints` and `app.domain.scheduling` reference each other's types (constraints take `CandidateAssignment`/`ScheduleState` in their method signatures; `app.domain.scheduling.factory`/`solver`/`optimizer` construct concrete constraint classes and `ConstraintEvaluator`) — a genuine two-way relationship, not an accident. Every `app/domain/constraints/*.py` file that needs a `scheduling` type only for a type hint imports it under `if TYPE_CHECKING:` (with `from __future__ import annotations` at the top of the file, so the hint itself is never evaluated at runtime) — this is what keeps `import app.domain.constraints` and `import app.domain.scheduling` both safe regardless of which one a caller happens to import first. A caller that imports constraint classes should do so from each constraint's own submodule (`app.domain.constraints.conflict`, not the aggregate `app.domain.constraints` package) for the same reason. Found the hard way in Phase 10: `tests/domain/scheduling/conftest.py` importing `app.domain.constraints` first (most test files import `app.domain.scheduling` first) triggered `ImportError: cannot import name ... from partially initialized module` — a real bug, not a test artifact, since it depended on import order alone.

## 8. TypeScript Conventions

- `strict: true` in `tsconfig.json`; no unchecked `any` — if a type is genuinely unknown, use `unknown` and narrow it.
- Prefer `type` for data shapes mirroring backend models, `interface` for component prop contracts (a documented convention, not a functional requirement — consistency matters more than the specific choice).
- No default exports for components (named exports only) — improves refactor/rename safety and IDE navigation.

## 9. React Conventions

- Function components + hooks only (no class components).
- One component per file; a component over ~200 lines is a signal to extract sub-components or hooks.
- Presentational components (`components/`) receive data via props only; data-fetching/business orchestration lives in `features/`/`pages/` (mirrors [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §8).
- Server state (API data) is not duplicated into ad hoc local `useState` — fetched data flows through a small dedicated data-fetching layer in `services/`/`hooks/` so cache/refresh behavior is centralized, not reimplemented per component.

**Frontend State** (referenced from [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §8; [01-CLAUDE.md](01-CLAUDE.md) rule 11 — implemented Phase 8):

- *Server state* (every API resource — catalog entities, availability, scheduling config, the schedule/versions/assignments, audit events): TanStack Query (`@tanstack/react-query`), one small hook module per resource under `hooks/` (`useCatalog.ts`, `useSchedule.ts`, `useAvailability.ts`, `useSchedulingConfig.ts`, `useAudit.ts`, `useSchool.ts`), each built on a typed `services/*Api.ts` client. *Decision:* this is the "small dedicated data-fetching layer" rule 11 requires, not a rejected "state-management library merely because it's popular" — it owns caching/refetch/invalidation for server data specifically, nothing else, and the seven catalog entities share one generic hook factory (`hooks/useCrud.ts`) mirroring the backend's own `build_crud_router` DRY choice.
- *Auth state* (identity, role, school_id): a single `AuthContext`/`useAuth` (`state/AuthContext.tsx`) combining Firebase's own auth state with the backend's `/auth/me` — the role is always read from the latter, never assumed from the Firebase user (docs/03-ARCHITECTURE.md #23-24).
- *UI/form state*: local `useState` inside the component/page that owns it (e.g. the selected schedule version, a move-in-progress form) — never lifted into a shared store.
- No Redux/Zustand/Jotai/etc.: with server state fully owned by TanStack Query and the only cross-cutting client state being auth, a general client-state store would duplicate what Query already does for server data and have nothing left to justify itself for the rest.
- Routing: `react-router-dom`, declarative `<Routes>`/`<Route>` (not the data-router/loader API) — route guards (`RequireAuth`, `RequireAdmin` in `components/RequireAuth.tsx`) are themselves just components composed into the tree, not a separate routing-state concern.

## 10. FastAPI Conventions

- One router module per domain resource (`api/routers/teachers.py`, `api/routers/schedules.py`, …), matching the endpoint groups in [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §26.
- Route handlers: parse/validate (via Pydantic + FastAPI dependencies) → call exactly one application-layer use case → map result to a response model. No business logic inline (Architecture Rule 4).
- Auth/role checks are FastAPI dependencies (`Depends(require_admin)`), never manual `if` checks copy-pasted per route.

## 11. Pydantic Conventions

- Separate models for API request, API response, and domain entity where their shapes genuinely differ (e.g., a response model omitting internal fields) — but avoid pointless 1:1 duplication when a domain entity's shape is already the correct API shape.
- Validation logic that is a *business rule* (e.g., "weeklyPeriods must be > 0") belongs in Pydantic field validators only for pure data-shape rules; cross-entity business rules (e.g., "requiredCapability must exist in the school's capability catalog") belong in the domain/application layer, not a Pydantic validator with hidden repository access.

## 12. Firebase Conventions

- All Firestore access goes through `infrastructure/repositories/*` and `infrastructure/firebase/*` — no `firestore_client.collection(...)` calls anywhere else in the codebase ([01-CLAUDE.md](01-CLAUDE.md) rule 6, [05-DATABASE.md](05-DATABASE.md) §2).
- Frontend Firebase usage is limited to the Auth SDK (`services/firebaseAuth.ts` or similar) — no `firebase/firestore` import in frontend code for business data.

## 13. Domain Layer Rules

- No imports from `fastapi`, `firebase_admin`, `google.cloud.firestore`, or any web/infra package anywhere under `domain/`.
- Domain services and the scheduling/rescheduling engines take plain domain objects as input/output — never Firestore document snapshots or Pydantic API models.

## 14. Application Layer Rules

- Use cases are the only place a repository interface is called from more than one domain object's perspective (orchestration) — domain services stay focused on pure logic.
- Use cases own the transaction/batch boundary ([04-DESIGN.md](04-DESIGN.md) §31); domain services never open a transaction themselves.

## 15. Infrastructure Layer Rules

- Repository implementations map Firestore document dicts ↔ domain entities explicitly (no reliance on implicit attribute-matching); this mapping is unit-tested against representative documents.
- Firebase Admin SDK initialization happens once, at startup, via dependency injection — never re-initialized per request.

## 16. API Conventions

- Resource-oriented URLs, plural nouns (`/teachers`, `/schedules`), verbs only for actions that aren't CRUD (`/schedules/generate`, `/schedules/{id}/reschedule`) per [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §26.
- Every endpoint has an OpenAPI-documented request/response schema (automatic via Pydantic + FastAPI) — no undocumented endpoints.

## 17. Error Handling

- Raise the specific `DomainError` subtype ([04-DESIGN.md](04-DESIGN.md) §24) closest to the actual failure; a single global exception handler in the API layer maps each to its HTTP status + JSON envelope.
- Never swallow an exception silently; if a failure is expected and handled, log it at an appropriate level and return a structured error — don't just `pass`.

## 18. Logging

- Use the module-level logger (`logging.getLogger(__name__)`), never `print()`.
- Log at generation/rescheduling start and end (with duration, counts, result status — [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §28), at auth failures, and at unexpected exceptions — not on every routine successful CRUD call (avoid log noise).
- Never log secrets, tokens, or full request bodies containing credentials.

## 19. Validation

- Schema validation (Pydantic) and domain validation ([04-DESIGN.md](04-DESIGN.md) §23) are both mandatory and serve different purposes — do not conflate them or skip one because the other exists.

## 20. Async Programming

- FastAPI route handlers that trigger generation/rescheduling are `async def` and dispatch the (CPU-bound) solver run to a background task/worker (e.g., `BackgroundTasks` or a dedicated task runner) so the event loop is never blocked by the solver's search loop — required for NFR-009 (UI responsiveness).
- The solver/optimizer code itself is synchronous, CPU-bound Python — it is not written as `async` internally (no I/O to await inside the search), which also keeps it simpler to reason about and test.
- Repository interfaces and their Firestore implementations (`app.infrastructure.repositories`) are synchronous (plain `def`, using the Firebase Admin SDK's standard `google.cloud.firestore.Client`), not `async def` against `AsyncClient`. *Decision:* wiring a separate async Firestore client would need its own credential/app plumbing alongside the Admin SDK's own (sync) one, for a benefit FastAPI already gets more simply — a `def` route handler (or an explicit `starlette.concurrency.run_in_threadpool` call from an `async def` one) runs in FastAPI's threadpool automatically, so a blocking Firestore call there doesn't stall the event loop. Reserve `async def` + background-task dispatch specifically for the CPU-bound solver/optimizer, per the point above — that's a different problem (a long-running computation, not blocking I/O) with a different fix.

## 21. Dependency Injection

- FastAPI's `Depends()` mechanism is the DI mechanism for the API layer (repositories, current-user resolution, use case construction).
- Application/domain code receives its dependencies (repositories, config) via constructor parameters — never reaches for a global singleton — so fakes can be substituted in tests.

## 22. Testing

- **Backend:** pytest, `tests/` mirrors `app/` structure. Domain/scheduling tests use no I/O at all. Application-layer tests use fake in-memory repository implementations (or the Firestore Emulator for integration coverage). API tests use FastAPI's `TestClient`.
- **Frontend:** Vitest + React Testing Library, colocated `*.test.tsx` next to the component/hook under test; test user-visible behavior (rendered text, interactions), not internal state.
- **E2E:** Playwright, limited to the critical workflows enumerated in [02-PRD.md](02-PRD.md) §15 and the demonstration scenario in [03-ARCHITECTURE.md](03-ARCHITECTURE.md) — not exhaustive path coverage (master prompt: "do not attempt to cover every possible path").
- **Property/invariant tests:** every generated/rescheduled `VALID` result is additionally checked, in a shared test helper, against the invariants in [02-PRD.md](02-PRD.md) §17 (no teacher/class/room overlap, no hard-constraint violation, all weekly requirements satisfied) — run against multiple benchmark scenarios (Small/Medium/Large, [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §30), not just one hand-picked example.

## 23. Mocking

- Prefer real, small, fast fakes (an in-memory `FakeTeacherRepository` implementing the real interface) over mocking-framework `Mock()` objects for repository interfaces — fakes catch interface-mismatch bugs that a loose `Mock()` would not.
- Use `unittest.mock`/`pytest-mock` only for true side-effecting boundaries (e.g., asserting a specific Firebase Admin SDK call was made) where a fake isn't practical.

## 24. Fixtures

- Shared `pytest` fixtures build representative `SchedulingProblem` instances (small/conflict-inducing/infeasible) once, reused across constraint and solver tests, to avoid duplicating scenario setup ([02-PRD.md](02-PRD.md) §15/§39 scenarios become fixtures directly).

## 25. Comments

- Explain *why*, not *what* — a non-obvious constraint interaction, a workaround for a specific Firestore limitation, a heuristic's rationale.
- Do not comment obvious code; do not leave commented-out code in commits.

## 26. Documentation

- Docstrings on public domain classes/functions covering: purpose, inputs, outputs, invariants, and complexity where relevant (mirrors [04-DESIGN.md](04-DESIGN.md) §29's complexity table) — especially for the solver, optimizer, and rescheduling engine ([01-CLAUDE.md](01-CLAUDE.md) §"Algorithm Documentation" cross-ref, master prompt §71).
- Any material deviation from what's specified in `docs/` must update the relevant document in the same change ([01-CLAUDE.md](01-CLAUDE.md) §14).

## 27. Security

- Every mutating and every teacher-scoped endpoint checks authorization server-side ([03-ARCHITECTURE.md](03-ARCHITECTURE.md) §24) — verified explicitly in API-layer tests (a request with the wrong role must fail, not just "happen to" fail).
- Run the `security-review` workflow before considering a security-relevant change (auth, roles, Firestore rules) complete.

## 28. Environment Variables

- All configuration that differs between environments (Firebase project ID, API base URL, solver defaults) is read from environment variables with no hardcoded fallback to a real value — only `.env.example` placeholders are committed.

## 29. Git

See [01-CLAUDE.md](01-CLAUDE.md) §15.

## 30. Commit Messages

Format: `type: short imperative description`, types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`. Examples (from the master prompt): `feat: implement teacher domain model`, `feat: add room availability validation`, `test: add scheduler constraint tests`, `fix: prevent duplicate room assignments`.

## 31. Pull Requests

- One coherent change per PR (one phase/feature slice, not a mix of unrelated fixes).
- PR description states: what changed, why, how it was tested, and which `docs/` sections (if any) were touched.

## 32. Code Review

- Every PR is checked against the Definition of Done ([01-CLAUDE.md](01-CLAUDE.md) §17) before merge.
- Reviewers specifically check: no hard constraint bypassed, no business logic leaked into the API/UI layers, no new dependency added without a §"Alternatives Considered"-style justification.

## 33. Refactoring

- Refactors are separate commits/PRs from behavior changes where practical, so a regression can be bisected to either "logic changed" or "logic moved."
- Never refactor and fix a bug in the same commit unless the refactor is the minimal fix itself.

## 34. Performance

- Optimize the solver's inner loop (candidate validity checks, forward checking) first, since it dominates generation time ([04-DESIGN.md](04-DESIGN.md) §29) — avoid premature micro-optimization elsewhere (e.g., CRUD endpoints) that isn't shown to matter by the benchmarks in [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §30.
- Prefer indexed dictionary lookups (`byTeacherSlot`, `byClassSlot`, `byRoomSlot`) over linear scans for conflict checks, as specified in the design.

## 35. Forbidden Practices

- Hardcoding domain data (teacher names, room IDs, subject codes) into scheduling algorithm code (master prompt §54).
- Subject-name string matching (`if subject == "Chemistry"`) instead of capability-based modeling (master prompt §55, HC-004).
- Silently bypassing, disabling, or softening a hard constraint.
- Direct Firestore access outside `infrastructure/` (frontend or backend).
- Placeholder/fake implementations presented as complete (`TODO: implement scheduler` in code claimed as done; hardcoded fake "Generate Schedule" results).
- Adding a dependency (library, service, database) without a documented justification in [06-TECH_STACK.md](06-TECH_STACK.md).
- Duplicating a business rule between frontend and backend as the source of truth (frontend may mirror simple UX validation only).
- `--no-verify`, disabling hooks, or bypassing lint/type-check gates to force a merge.
