# 01-CLAUDE.md — Instructions for Claude Code Sessions

## 1. Project Identity

**Name:** TimeForge

**Type:** Software Engineering Final Project — a constraint-based school timetabling and dynamic rescheduling platform.

**One-line description:** TimeForge generates, validates, optimizes, and dynamically reschedules school timetables while satisfying mandatory scheduling rules and optimizing for quality and stability.

This is **not** an AI/ML project. No LLMs, predictive models, or ML frameworks are part of the scheduling engine. The engine is a classical constraint-satisfaction and local-search system.

## 2. Project Purpose

Schools need to assign lessons (subject × class) to teachers, time periods, and rooms without conflicts, while respecting availability, room capabilities, and workload rules, and while optimizing for preferences and schedule quality. When real-world disruptions occur (teacher absence, room closure), the system must repair the existing schedule with minimal disruption rather than regenerating it from scratch.

## 3. Domain Overview

Read [02-PRD.md](02-PRD.md) for full domain and requirements detail. Core concepts:

- **School** configures days, periods, breaks, classes, teachers, subjects, rooms.
- **LessonRequirement** expresses "Class X needs N periods/week of Subject Y" (optionally requiring a room capability).
- The **scheduling engine** expands requirements into unplaced **Lesson** instances and assigns each a teacher, room, and time slot, producing **ScheduleAssignment** records that make up a **ScheduleVersion**.
- **Hard constraints** (HC-xxx) must never be violated in a valid schedule. **Soft constraints** (SC-xxx) are optimized but may be traded off.
- **Rescheduling** repairs an existing published schedule after a disruption, producing a new **ScheduleVersion** while minimizing changes.
- All persistent state lives in **Firebase Firestore**. **Firebase Authentication** handles identity.

## 4. Technology Stack

See [06-TECH_STACK.md](06-TECH_STACK.md) for full rationale. Summary:

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| Backend API | Python + FastAPI + Pydantic |
| Scheduling engine | Pure Python (no framework/DB dependency) |
| Database | Firebase Firestore (sole persistent store) |
| Auth | Firebase Authentication |
| Backend tests | pytest |
| Frontend tests | Vitest + React Testing Library |
| E2E tests | Playwright |
| Python quality | Ruff |
| Frontend quality | ESLint + Prettier |
| Docs | Markdown + Mermaid |

**Never introduce:** PostgreSQL, MySQL, MongoDB, SQLite (as production DB), Supabase, DynamoDB, Redis-as-database, Kafka, Kubernetes, microservices, or any ML/LLM library — unless the user explicitly approves a documented architectural change.

## 5. Repository Expectations

Expected top-level layout (see [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §8 and [07-CODE_STANDARDS.md](07-CODE_STANDARDS.md) for full structure):

```text
TimeForge/
├── docs/           # the seven foundation documents (source of truth)
├── backend/        # FastAPI app, domain, scheduling engine, infrastructure
├── frontend/        # React + TypeScript + Vite app
├── tests/          # cross-cutting / integration / e2e tests not colocated
├── scripts/        # dev scripts (seed data, emulator bootstrap)
├── .env.example
├── .gitignore
└── README.md
```

Before making changes, always re-read this file and the specific document relevant to the change (PRD for requirements, ARCHITECTURE for structure, DESIGN for algorithms, DATABASE for persistence, CODE_STANDARDS for style).

## 6. Architecture Rules (Mandatory)

1. The **scheduling engine** (`backend/app/domain/scheduling/`) MUST NOT import FastAPI.
2. The **scheduling engine** MUST NOT import Firebase/Firestore clients.
3. The **domain layer** (`backend/app/domain/`) MUST NOT depend on Firebase directly — only on repository *interfaces* defined in the domain/application layer.
4. **API route handlers** MUST NOT contain business logic — they parse/validate input, call an application service, and map the result to a response model.
5. **React components** MUST NOT contain scheduling/business logic — that logic lives in the backend; the frontend renders state and calls the API.
6. Firestore access MUST be centralized in `backend/app/infrastructure/repositories/` — never scattered inline in route handlers or services.
7. All schedule mutations (manual edits, generation, rescheduling) MUST pass through domain/application validation before persistence.
8. Hard constraints MUST NEVER be silently bypassed, disabled, or downgraded to warnings without an explicit, documented, user-approved decision.
9. Do not add dependencies without justification recorded in [06-TECH_STACK.md](06-TECH_STACK.md).
10. Do not modify unrelated files in the course of a focused change.
11. Business rules MUST NOT be duplicated between frontend and backend — the backend is authoritative; the frontend may mirror simple validation for UX only, never as the source of truth.

## 7. Domain Rules

- Every `ScheduleAssignment` must reference a valid `Lesson`, `Teacher`, `Class`, `TimePeriod`, and `Room`.
- A `Room` assigned to a lesson requiring a capability MUST have that capability (HC-004).
- Room `capacity` MUST NOT be exceeded by the assigned class's student count (HC-009).
- Entities are never deleted destructively if referenced by a published schedule — use status/archival fields (see [05-DATABASE.md](05-DATABASE.md) §"Data Retention").

## 8. Scheduling Engine Rules

- The engine's public interface is `SchedulingProblem -> ScheduleResult`. See [04-DESIGN.md](04-DESIGN.md) §15 for the algorithm.
- The engine must remain deterministic given the same problem, seed, and configuration (see [07-CODE_STANDARDS.md](07-CODE_STANDARDS.md) §"Scheduling").
- Every hard constraint is implemented as an independent, unit-testable class implementing a common `HardConstraint` interface — never as inline conditionals mixed together.
- Every soft constraint is implemented as an independent `SoftConstraint` evaluator contributing a weighted penalty to a single, explainable score.
- The rescheduling engine reuses the same constraint evaluators as initial generation — never a parallel, divergent rule set.

## 9. Firebase Rules

- Firestore access happens only through repository classes in `backend/app/infrastructure/firebase/` and `backend/app/infrastructure/repositories/`.
- The frontend uses Firebase Authentication directly (for login/session), but MUST NOT write business data directly to Firestore — all business mutations go through the backend API.
- Never commit service account keys, `.env`, or any credential file. Use `.env.example` with placeholder values only.
- Unit tests must not require live production Firebase; use the Firestore Emulator or in-memory fakes implementing the repository interfaces.

## 10. API Rules

- Organize routes by domain resource (see [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §26).
- Every endpoint has an explicit Pydantic request/response model — no raw dicts.
- Every endpoint enforces authentication and role-based authorization server-side — never trust client-supplied role claims.
- Errors map to the structured error model in [04-DESIGN.md](04-DESIGN.md) §24; never leak stack traces to clients.

## 11. Frontend Rules

- State is separated by concern (auth, school data, schedule data, UI/form state) — no single global store holding everything.
- Do not add a state-management library merely because it is popular; justify it against the actual complexity.
- All schedule-changing actions call the backend and render the backend's validation result — the frontend never decides a move is valid on its own.

## 12. Testing Rules

- No feature is complete without tests (see Definition of Done, §17).
- The scheduling engine requires the heaviest test investment: unit tests per constraint, integration tests per scenario in [02-PRD.md](02-PRD.md) §"Acceptance Criteria", and invariant/property tests (no double-booking, requirements satisfied) run against every generated schedule in tests.
- Never delete or weaken a test merely to make a build pass — fix the underlying cause or, if the test's premise is wrong, explain why and get confirmation before changing it.

## 13. Security Rules

- Authorization is enforced in the backend on every mutating and every teacher-scoped read endpoint.
- Validate all input at the API boundary with Pydantic; never trust client-supplied IDs to imply ownership without a server-side check.
- Follow the Firestore security rules in [05-DATABASE.md](05-DATABASE.md) §"Security Rules" as defense-in-depth, even though the backend Admin SDK is the primary authorization gate.

## 14. Documentation Rules

- If a change materially alters architecture, domain model, database schema, or algorithm behavior, update the relevant document(s) in the same change — do not let docs drift from code.
- Record any new major decision using the "Decision" format used throughout these documents (see [02-PRD.md](02-PRD.md) §"Assumptions & Decisions").

## 15. Git Rules

- Commit messages: `type: short description` (`feat`, `fix`, `test`, `docs`, `refactor`, `chore`) — see [07-CODE_STANDARDS.md](07-CODE_STANDARDS.md) §"Commit Messages".
- Small, coherent commits. No unrelated changes bundled together.
- Never force-push, rewrite history, or bypass hooks without explicit user approval.

## 16. Change Management

- Major architectural changes (new dependency category, new persistent store, new service boundary) require explicit user approval before implementation.
- Minor implementation details may use reasonable engineering judgment consistent with these documents.
- When a requirement is ambiguous, document the ambiguity and the chosen resolution rather than silently deciding a major product behavior.

## 17. Definition of Done

A feature is complete only when:

- [ ] Implementation matches the design in [04-DESIGN.md](04-DESIGN.md) (or the design was updated to match a justified change).
- [ ] Unit tests exist and pass.
- [ ] Integration tests exist where the feature crosses a layer boundary.
- [ ] Type checking passes (`mypy`/`pyright` per config, TS strict mode).
- [ ] Lint passes (Ruff, ESLint).
- [ ] Error handling follows the structured error model.
- [ ] Security/authorization implications considered.
- [ ] Relevant documentation updated.
- [ ] No unrelated files changed.
- [ ] No fake/placeholder functionality (see §18).

## 18. Forbidden Behavior

- No UI buttons wired to functionality that doesn't work.
- No hardcoded/fake "Generate Schedule" results.
- No `TODO: implement scheduler`-style placeholders left in code presented as done.
- No magic values (teacher names, room IDs, subject codes) hardcoded into scheduling algorithms — all such data comes from the domain/config.
- No `if subject == "Chemistry"` style special-casing — model room requirements via capabilities (HC-004).
- No silent bypass of hard constraints.
- No business logic embedded in Firestore security rules as the sole authorization mechanism (backend must still enforce authorization).

## 19. Agent Workflow

1. Understand the request.
2. Read the relevant document(s) from `docs/`.
3. Inspect existing code touching the affected area.
4. Identify affected modules and layer boundaries.
5. Identify requirements/constraints from [02-PRD.md](02-PRD.md).
6. Produce a short plan (use plan mode for non-trivial work).
7. Implement the smallest correct change.
8. Add/update tests.
9. Run tests, type checks, lint.
10. Review the diff for unrelated changes.
11. Update documentation if the change affects it.
12. Report what changed and how it was validated.

## 20. Troubleshooting Principles

- Identify the root cause before patching symptoms.
- Re-check architecture and design docs before introducing a workaround.
- Do not weaken a hard constraint or delete a failing test to make the problem "go away."
- Prefer the smallest correct fix; avoid speculative refactors while fixing a bug.
