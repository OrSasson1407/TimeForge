# 02-PRD.md — Product Requirements Document

## 1. Executive Summary

TimeForge is a constraint-based platform for generating, validating, optimizing, and dynamically rescheduling school timetables. It replaces manual, error-prone, spreadsheet-based scheduling with an engine that guarantees zero hard-constraint violations, optimizes for teacher/class preferences and schedule quality, explains its decisions, and — critically — repairs an existing published schedule with minimal disruption when real-world changes occur (teacher absence, room closure, new requirements) instead of regenerating it from scratch.

## 2. Product Vision

> Generate and continuously maintain a high-quality school timetable that satisfies all mandatory constraints while optimizing preferences and minimizing disruption when changes occur.

TimeForge is not a one-time generator. It is a system of record for the school's timetable across its entire lifecycle: draft, published, and every subsequent revision.

## 3. Problem Statement

Manual timetabling is combinatorially hard: dozens of teachers, classes, subjects, and specialized rooms must be arranged across a fixed weekly grid without conflicts, while respecting availability and workload rules. Spreadsheet-based processes:

- Cannot systematically guarantee zero conflicts at scale.
- Cannot explain *why* a slot was chosen or *why* generation failed.
- Treat every mid-year change (a sick teacher, a closed lab) as a from-scratch redo, causing far more disruption than necessary.
- Provide no audit trail of who changed what and why.

## 4. Current Problem / Pain Points

- Administrators spend days manually resolving conflicts after each change to teacher/room availability.
- There is no systematic way to know a full schedule is even *possible* before hours are spent trying.
- Teachers have no visibility into their own schedule changes or a channel to submit availability/preferences.
- Historical schedule versions are lost once a new version is created ad hoc (e.g., overwritten spreadsheets).

## 5. Target Users

- **School administrators / schedule coordinators** — configure the school, generate and publish timetables, handle disruptions.
- **Teachers** — view their timetable, submit availability and preferences.

## 6. Personas

**Dana, Vice Principal (Administrator).** Responsible for the whole school's timetable. Needs to generate a valid schedule quickly at the start of the year and handle several disruptions per week (illness, room maintenance) without redoing everyone's schedule.

**Yossi, Chemistry Teacher.** Teaches at two grade levels, needs specific lab access, has two fixed afternoons unavailable for personal reasons. Wants to see his own timetable and be notified when it changes.

## 7. Goals

- G1: Generate hard-constraint-valid timetables for realistic school sizes (tens of classes, dozens of teachers, hundreds of weekly lessons) within a practical time budget.
- G2: Optimize soft constraints to produce a demonstrably better-than-random-valid schedule, with an explainable quality score.
- G3: Detect and clearly explain infeasibility instead of failing silently.
- G4: Support safe manual editing with real-time conflict validation.
- G5: Support dynamic rescheduling that minimizes disruption and explains every automatic change.
- G6: Maintain a versioned, auditable history of the timetable.
- G7: Enforce role-based access so only authorized users can modify schedules.

## 8. Non-Goals

- Not a general-purpose university/exam-scheduling system (no cross-institution rooming markets).
- Not a student information system (grades, attendance, enrollment management are out of scope).
- Not a communication/notification platform beyond in-app schedule visibility (no SMS/push infrastructure in MVP).
- Not an AI/ML system — no predictive or generative model is used for scheduling decisions.

## 9. Product Scope

In scope: school configuration, teacher/class/subject/room management, availability and preferences, constraint-based generation, quality scoring, infeasibility diagnostics, manual editing with validation, dynamic rescheduling, versioning, publishing, audit logging, role-based authentication.

Out of scope (see §11 Future Scope): individual student-level scheduling, split/combined classes, substitute-teacher workflows, user-authored custom constraint types, multi-school/multi-tenant billing, notifications infrastructure.

## 10. MVP

The MVP must include, end-to-end and working (not mocked):

- School configuration: days, periods, breaks.
- CRUD for teachers, classes, subjects, rooms (with capabilities), lesson requirements.
- Availability management for teachers and classes.
- Hard constraints HC-001..HC-009 enforced without exception.
- Soft constraints SC-001..SC-010 optimized with a configurable weight model.
- Schedule generation with progress reporting and a quality report.
- Infeasibility diagnostics with bottleneck identification.
- Manual assignment editing with validate/apply and conflict explanation.
- Schedule versioning (draft/published/archived) with comparison and history.
- Dynamic rescheduling for teacher absence and room unavailability, with disruption minimization and change explanations.
- Audit log for all significant mutations.
- Firebase Authentication with Administrator and Teacher roles, enforced server-side.
- Seed data for a realistic demo school.

## 11. Future Scope

**Version 2 (planned, not MVP):**
- Substitute-teacher assignment workflow.
- Configurable custom constraints authored by administrators (parameterized, not arbitrary code).
- Student-level scheduling / electives / split & combined classes.
- Multi-period (semester/term) schedule support.
- Notification delivery (email/push) on schedule changes.

**Future (explicitly excluded from this project):**
- Multi-school/tenant SaaS billing and provisioning.
- Mobile native apps.
- AI/ML-based recommendation of preferences.

## 12. Functional Requirements

| ID | Requirement |
|---|---|
| FR-001 | Administrators can define a school's days, periods (with start/end times), and breaks. |
| FR-002 | Administrators can perform CRUD on Teachers, including subjects taught, classes taught, availability, preferences, and workload limits. |
| FR-003 | Administrators can perform CRUD on Classes, including grade, student count, home room, and availability. |
| FR-004 | Administrators can perform CRUD on Subjects, including required weekly periods, required room capability, preferred periods/days, and spacing rules. |
| FR-005 | Administrators can perform CRUD on Rooms, including capacity, type, capabilities, and availability. |
| FR-006 | Administrators can define Lesson Requirements linking a Class and Subject to a weekly period count and optional room capability. |
| FR-007 | Teachers can view their own timetable. |
| FR-008 | Teachers can submit their own availability and preferences. |
| FR-009 | Administrators can trigger schedule generation for a school and receive progress updates. |
| FR-010 | The system validates a scheduling problem before attempting generation and reports structural issues (e.g., zero available rooms with a required capability). |
| FR-011 | The system produces a schedule that satisfies all hard constraints (HC-001..HC-009) or reports INFEASIBLE with a diagnostic. |
| FR-012 | The system computes a quality score for a generated schedule based on soft constraint penalties. |
| FR-013 | Administrators can view a full timetable by class, by teacher, or by room. |
| FR-014 | Administrators can propose a manual move of an assignment (change period/room/teacher) and receive a VALID/WARNING/INVALID result with an explanation before applying it. |
| FR-015 | Administrators can apply a validated manual move, creating an audit entry. |
| FR-016 | The system supports schedule versions with status Draft, Published, Archived. |
| FR-017 | Administrators can publish a Draft version, making it the active schedule. |
| FR-018 | Administrators can compare two schedule versions and see a diff summary. |
| FR-019 | Administrators can view a chronological version history with author and reason. |
| FR-020 | Administrators can report a disruption event (teacher unavailable, room closed) and trigger rescheduling. |
| FR-021 | The rescheduling engine produces a new Draft version that preserves unaffected assignments and minimizes disruption cost. |
| FR-022 | The system explains each automatically changed assignment (reason, alternatives considered, why the choice was selected). |
| FR-023 | The system records an audit event for every significant mutation (generation, publish, manual move, rescheduling, availability/constraint change). |
| FR-024 | The system authenticates users via Firebase Authentication and enforces Administrator/Teacher roles server-side on every relevant endpoint. |
| FR-025 | When no valid schedule exists, the system reports the specific constraint/resource bottleneck, affected entities, and shortage quantity. |

## 13. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-001 | Schedule generation for a benchmark school (≈50 classes, ≈100 teachers, ≈500 weekly lessons) completes within a documented, measured time budget (see [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §"Performance"); the engine reports TIMEOUT rather than hanging indefinitely. |
| NFR-002 | Manual move validation returns a result within ~1 second for interactive use. |
| NFR-003 | All backend mutation endpoints enforce authentication and authorization; unauthorized requests receive 401/403, never partial data. |
| NFR-004 | The system does not lose data on concurrent edits — conflicting writes are detected and rejected with a clear error, never silently overwritten (see [05-DATABASE.md](05-DATABASE.md) §"Concurrency"). |
| NFR-005 | The scheduling engine has no dependency on FastAPI or Firebase and can run and be tested in complete isolation. |
| NFR-006 | The system logs generation/rescheduling runs with duration, problem size, violation counts, and score, without logging credentials or secrets. |
| NFR-007 | Core scheduling algorithm behavior is deterministic given the same problem input and configured random seed, to keep it testable and explainable. |
| NFR-008 | Frontend and backend maintain automated test suites (unit, integration, and for the frontend, component tests) runnable in CI without live production Firebase credentials. |
| NFR-009 | The UI remains responsive during schedule generation (async operation with progress reporting), never blocking the browser thread. |

## 14. User Stories

- As an administrator, I want to define my school's period grid once so all subsequent scheduling respects it.
- As an administrator, I want to generate a first timetable and see its quality score so I can judge if it's usable.
- As an administrator, I want to know exactly why generation failed so I can fix the root cause (e.g., add a lab) instead of guessing.
- As an administrator, I want to move a lesson manually and be warned immediately if it creates a conflict.
- As an administrator, I want to mark a teacher unavailable next Tuesday and get a minimally-disruptive updated schedule.
- As a teacher, I want to see my own timetable and submit my availability without needing administrator help.
- As an administrator, I want a history of every schedule version so I can see what changed and why.

## 15. Acceptance Criteria

Representative scenarios (used directly as integration test scenarios, see [07-CODE_STANDARDS.md](07-CODE_STANDARDS.md) §"Testing"):

1. **Simple valid case:** 2 classes, 2 teachers, 2 rooms, no conflicting requirements → generation returns VALID with 0 hard violations.
2. **Teacher double-booking is rejected:** A manually proposed move that assigns a teacher to two simultaneous lessons → INVALID with a teacher-conflict explanation.
3. **Lab shortage is infeasible:** Weekly chemistry-lab period demand exceeds lab supply → generation returns INFEASIBLE with a bottleneck report naming the resource and shortage.
4. **Teacher absence triggers repair:** A published schedule plus a teacher-unavailable event → rescheduling returns a new Draft version where only the affected teacher's assignments (and their knock-on conflicts) changed, all hard constraints still hold.
5. **No alternative exists:** A disruption with no feasible replacement slot → rescheduling reports which lessons could not be repaired and why.
6. **Valid manual move:** A move to a free, compatible slot → VALID, applied, and audited.
7. **Version comparison:** Two versions differing by 8 assignments → diff view lists exactly those 8 changes.

## 16. Business Rules

| ID | Rule |
|---|---|
| BR-001 | A published schedule version is the single source of truth for "the current timetable" until a newer version is published. |
| BR-002 | Only Administrators may publish, manually edit, or trigger (re)scheduling. |
| BR-003 | Teachers may only modify their own availability/preferences, never another teacher's. |
| BR-004 | Every mutation to a published schedule must create a new version — a published version's assignment data, once published, is not edited in place. |
| BR-005 | A schedule cannot be published while it has unresolved hard-constraint violations. |
| BR-006 | Deleting a Teacher/Class/Room/Subject referenced by any non-archived schedule version is blocked; it must be deactivated instead. |

## 17. Hard Constraints (must always hold in any VALID schedule)

| ID | Constraint |
|---|---|
| HC-001 | A teacher cannot be assigned to two lessons in the same time period. |
| HC-002 | A class cannot be assigned to two lessons in the same time period. |
| HC-003 | A room cannot host two lessons in the same time period. |
| HC-004 | A lesson requiring a room capability must be assigned a room that has that capability. |
| HC-005 | A teacher cannot be assigned outside their declared availability. |
| HC-006 | A class cannot be assigned outside its declared availability. |
| HC-007 | No lesson may be assigned to a period marked as a mandatory break. |
| HC-008 | Every lesson requirement's weekly period count must be fully satisfied in a VALID schedule. |
| HC-009 | A room's assigned class size must not exceed the room's capacity. |

## 18. Soft Constraints (optimized, may be traded off)

| ID | Constraint |
|---|---|
| SC-001 | Prefer a teacher's declared preferred periods. |
| SC-002 | Prefer a teacher's declared preferred days. |
| SC-003 | Minimize gaps (idle periods) in a teacher's daily schedule. |
| SC-004 | Distribute a subject's weekly lessons across different days rather than clustering them. |
| SC-005 | Avoid excessive consecutive lessons of the same subject for a class. |
| SC-006 | Balance each class's daily lesson load across the week. |
| SC-007 | Prefer a class's home room when no special capability is required. |
| SC-008 | Optimize utilization of shared/specialized resources (minimize idle specialized-room time where demand exists). |
| SC-009 | Minimize disruption (moved assignments, changed rooms/teachers) during rescheduling. |
| SC-010 | Preserve previously published assignments when regenerating or repairing, when doing so doesn't harm other objectives. |

## 19. Initial Generation

See FR-009..FR-012 and [04-DESIGN.md](04-DESIGN.md) §15 for the algorithm. Generation is asynchronous, reports progress, and always terminates with one of: VALID, INFEASIBLE, FAILED, TIMEOUT (see §"Solver Requirements" in [03-ARCHITECTURE.md](03-ARCHITECTURE.md)).

## 20. Dynamic Rescheduling

See FR-020..FR-022. Rescheduling is a distinct engine mode (not a full regeneration): it identifies the minimal affected subset, freezes everything else, searches for repairs, and reports a disruption-cost summary (see [04-DESIGN.md](04-DESIGN.md) §17).

## 21. Manual Editing

See FR-014..FR-015. Every proposed move is validated server-side before being offered for application; every applied move is audited.

## 22. Conflict Detection

Conflict detection is the shared mechanism behind manual-move validation, generation, and rescheduling — the same hard-constraint evaluators are reused in all three (see [01-CLAUDE.md](01-CLAUDE.md) §8).

## 23. Infeasibility Diagnostics

See FR-025 and [04-DESIGN.md](04-DESIGN.md) §19 for the bottleneck-analysis algorithm.

## 24. Versioning

See FR-016..FR-019, BR-004, and [05-DATABASE.md](05-DATABASE.md) for the persistence model (Decision: hybrid — per-version assignment subcollection plus version metadata; see database doc §"Versioning Strategy").

## 25. Publishing

See BR-001, BR-005. Publishing is a controlled state transition, not an assignment-level edit.

## 26. Audit

See FR-023 and [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §"Audit". Every audit entry: actor, timestamp, operation, entity, previous value, new value, reason (where applicable).

## 27. Roles

**Administrator** — full configuration and schedule control (§"Business Rules" BR-002).
**Teacher** — view own schedule; manage own availability/preferences (BR-003).

*Decision:* A third "Scheduler/Coordinator" role (subset of admin permissions) is deferred to Future Scope — MVP ships with exactly two roles to keep the authorization model simple and testable.

## 28. Permissions

| Action | Administrator | Teacher |
|---|---|---|
| Configure school/teachers/classes/subjects/rooms | ✅ | ❌ |
| Generate/reschedule/publish | ✅ | ❌ |
| Manually edit assignments | ✅ | ❌ |
| View full timetable (any class/teacher/room) | ✅ | ✅ (read-only) |
| View own timetable | ✅ | ✅ |
| Submit own availability/preferences | ✅ | ✅ |
| Submit another teacher's availability | ❌ | ❌ |
| View audit log | ✅ | ❌ |

## 29. Notifications

*Decision:* Out of MVP scope (see Future Scope). In-app visibility of schedule changes (via version history and the teacher's own timetable view) satisfies MVP needs without building notification infrastructure.

## 30. Error Handling

See [04-DESIGN.md](04-DESIGN.md) §"Error Model" for the full structured error taxonomy (ValidationError, ConflictError, AuthorizationError, NotFoundError, SchedulingError, InfeasibleScheduleError, ReschedulingError, ConcurrencyError). API responses are predictable and never leak internals (NFR-003, [01-CLAUDE.md](01-CLAUDE.md) §10).

## 31. Edge Cases

See [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §"Edge Case Analysis" for the full list (no available teacher/room/lab, over-constrained availability, resource bottlenecks, concurrent edits, generation timeout, duplicate generation requests, published-version immutability, etc.).

## 32. Performance

Target benchmark scenarios and measured results are documented in [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §"Performance" once implemented; no numbers are fabricated ahead of actual benchmarking (Small/Medium/Large scenarios per the master prompt).

## 33. Security

See §27–28 above and [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §"Security". Backend is the sole authorization authority; Firestore rules are defense-in-depth.

## 34. Usability

The UI must communicate long-running generation/rescheduling progress (never freeze), show clear VALID/WARNING/INVALID states, and explain every automatic decision in plain language (see [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §"Explanation System").

## 35. Success Metrics

- 0 hard-constraint violations in any published schedule (measured by the invariant test suite run against every generated/rescheduled result).
- Rescheduling changes materially fewer assignments than a full regeneration would, for the same disruption (measured and reported per event, per SC-009).
- All MVP functional requirements (§12) demonstrably working end-to-end in the demo scenario (§"Demonstration Scenario" in ARCHITECTURE).

## 36. Risks

- **Combinatorial blow-up** at larger school sizes could make generation slow — mitigated by heuristic ordering (MRV/degree/LCV) and a documented timeout with graceful TIMEOUT status.
- **Firestore document/query limits** could complicate large-schedule reads — mitigated by the assignment-subcollection design (see [05-DATABASE.md](05-DATABASE.md)).
- **Firestore emulator drift from production** could hide bugs — mitigated by keeping emulator and production on the same Firestore rules/version and running a subset of tests against a real (non-production) Firebase project before release.
- **Scope creep** into full SIS territory — mitigated by the explicit Non-Goals in §8.

## 37. Assumptions & Decisions

- *Decision:* MVP does not model individual students — only per-class aggregate `studentCount`. Reason: individual student scheduling (electives, split groups) adds a second combinatorial dimension not required to demonstrate the core scheduling/rescheduling engineering challenge.
- *Decision:* Constraints are configurable in their *parameters/weights*, not user-authored as arbitrary logic, in MVP. Reason: keeps the constraint engine closed, testable, and safe; open-ended user-defined rules are Version 2 scope.
- *Decision:* Rescheduling and generation share one solver core (see [04-DESIGN.md](04-DESIGN.md)) rather than two separate algorithms. Reason: avoids duplicated, potentially inconsistent constraint logic (violates architecture rule against duplicating business rules).
- *Assumption:* A single school per deployment in MVP (no multi-tenant switching in the UI), though the data model supports multiple `School` documents for testing/demo purposes.

## 38. Open Questions

- Should published schedules be fully immutable (requiring a new version for *any* change) or allow trivial metadata edits in place? *Current decision: fully immutable per BR-004; revisit only if this proves too rigid in practice.*
- Should optimization weights be editable by administrators via the UI in MVP, or fixed/config-file-only? *Revised in Phase 8: configurable via a config document (see [05-DATABASE.md](05-DATABASE.md)), editable through an admin-only API (Phase 7) and a small dedicated weight-tuning screen (`frontend/src/pages/ConstraintsPage.tsx`, Phase 8) — the original "no dedicated UI in MVP" call was reconsidered once the API already existed and the screen turned out to be a thin, low-effort form over it, not a reason to leave the feature admin-inaccessible.*
- Should teachers be able to lock a specific assignment against automatic rescheduling? *Deferred to Version 2.*
- How long should archived schedule versions be retained? *See [05-DATABASE.md](05-DATABASE.md) §"Data Retention" for the proposed default and rationale.*
