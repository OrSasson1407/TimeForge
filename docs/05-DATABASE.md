# 05-DATABASE.md — Firestore Database Design

The **only** persistent database is **Firebase Firestore**. No relational or other NoSQL database is introduced anywhere in this system.

## 1. Database Goals

- Support the query patterns actually needed by the API (§8), not a generic relational mirror.
- Respect Firestore's constraints: 1 MiB document size limit, no server-side joins, limited compound queries without indexes, per-document write-contention costs.
- Keep hard-constraint-critical reads (a version's full assignment set) cheap and consistent.
- Support optimistic concurrency and atomic multi-document updates where the domain requires them ([04-DESIGN.md](04-DESIGN.md) §30–31).
- Keep audit history complete and immutable.

## 2. Firestore Architecture

Firestore is used purely as a **structured document store with backend-mediated access**: the FastAPI backend (via the Admin SDK) is the sole writer of business data; the frontend only uses Firebase Authentication, never direct Firestore business writes ([01-CLAUDE.md](01-CLAUDE.md) rule 6, [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §25). Firestore Security Rules (§10) are configured as defense-in-depth, not as the primary authorization mechanism.

## 3. Collections

Top-level and nested collections:

```text
schools/{schoolId}
schools/{schoolId}/teachers/{teacherId}
schools/{schoolId}/classes/{classId}
schools/{schoolId}/subjects/{subjectId}
schools/{schoolId}/rooms/{roomId}
schools/{schoolId}/schoolDays/{dayId}
schools/{schoolId}/timePeriods/{periodId}
schools/{schoolId}/lessonRequirements/{requirementId}
schools/{schoolId}/availability/{availabilityId}
schools/{schoolId}/schedulingConfig/current            # single config doc

schedules/{scheduleId}
schedules/{scheduleId}/versions/{versionId}
schedules/{scheduleId}/versions/{versionId}/assignments/{assignmentId}
schedules/{scheduleId}/reschedulingEvents/{eventId}

users/{userId}                                          # role mapping, backend-managed

auditEvents/{auditEventId}
```

*Decision:* configuration entities (teachers, classes, subjects, rooms, days, periods, availability) are **subcollections of `schools/{schoolId}`** because they are always queried scoped to one school and never across schools — this keeps security rules simple (`match /schools/{schoolId}/{document=**}`) and avoids a `schoolId` filter on every top-level query. `schedules` and `auditEvents` are top-level because audit events reference many entity types and don't benefit from nesting, and a schedule's identity outlives any single school-config edit.

## 4. Documents

Representative document shapes (illustrative, not exhaustive):

```json
// schools/{schoolId}
{
  "name": "Northgate High School",
  "timezone": "Asia/Jerusalem",
  "createdAt": "2026-01-05T08:00:00Z"
}
```

```json
// schools/{schoolId}/rooms/{roomId}
{
  "name": "Room 301",
  "capacity": 35,
  "type": "LABORATORY",
  "capabilities": ["CHEMISTRY_LAB", "PROJECTOR"],
  "status": "ACTIVE"
}
```

```json
// schools/{schoolId}/lessonRequirements/{requirementId}
{
  "classId": "class_7A",
  "subjectId": "subject_chemistry",
  "weeklyPeriods": 3,
  "requiredCapability": "CHEMISTRY_LAB"
}
```

```json
// schools/{schoolId}/availability/{availabilityId}
// dayId omitted (null) -> applies to this TimePeriod on every active day;
// set -> applies to that specific (day, period) only, taking priority over
// a day-independent record for the same owner+period (docs/04-DESIGN.md #2).
{
  "ownerType": "TEACHER",
  "ownerId": "teacher_123",
  "dayId": null,
  "timePeriodId": "period_3",
  "isAvailable": false,
  "preferenceWeight": 0
}
```

```json
// schedules/{scheduleId}
{
  "schoolId": "school_abc",
  "activeVersionId": "version_7"
}
```

```json
// schedules/{scheduleId}/versions/{versionId}
{
  "status": "PUBLISHED",
  "parentVersionId": "version_6",
  "versionTag": 4,
  "score": { "hardViolations": 0, "softPenalty": 42.6, "quality": 87.4 },
  "assignmentCount": 512,
  "createdBy": "user_dana",
  "createdAt": "2026-02-01T09:00:00Z",
  "reason": "Initial generation for spring term",
  "requestId": "req_8f2a1c"
}
```

```json
// schedules/{scheduleId}/versions/{versionId}/assignments/{assignmentId}
{
  "lessonId": "lesson_math_7A_3",
  "teacherId": "teacher_123",
  "classId": "class_7A",
  "roomId": "room_101",
  "dayId": "day_mon",
  "timePeriodId": "period_mon_3"
}
```

```json
// schedules/{scheduleId}/reschedulingEvents/{eventId} (Phase 9)
{
  "type": "TEACHER_UNAVAILABLE",
  "targetEntityId": "teacher_123",
  "affectedSlots": [{ "dayId": "day_tue", "timePeriodId": "period_tue_3" }],
  "reason": "Teacher unavailable Tue P3",
  "reportedAt": "2026-02-03T14:20:00Z"
}
```

```json
// auditEvents/{auditEventId}
{
  "actor": { "userId": "user_dana", "role": "ADMIN" },
  "timestamp": "2026-02-03T14:22:00Z",
  "operation": "RESCHEDULED",
  "entityType": "SCHEDULE_VERSION",
  "entityId": "version_8",
  "before": null,
  "after": { "movedAssignments": 14, "directlyAffectedLessonCount": 3 },
  "reason": "Teacher unavailable Tue P3"
}
```

## 5. Subcollections

Used precisely where data is (a) always scoped to a parent and (b) potentially unbounded/large: `versions/{versionId}/assignments` (hundreds of documents per version), `schools/{schoolId}/*` config collections. Avoided for small, bounded, always-together data (e.g., a version's `score` is an embedded map, not a separate document — §6).

## 6. References

Documents reference related entities **by ID string** (e.g., `ScheduleAssignment.teacherId`), never by embedding full related documents — Firestore has no server-side joins, so the backend resolves references via repository-level batched `get()` calls, and the domain layer works with fully-resolved objects (repositories hide the reference-resolution from the domain, per [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §8).

## 7. Denormalization Strategy

Denormalize only where it avoids an N-document read for a common query:
- `ScheduleVersion.assignmentCount` and `.score` are denormalized summaries (avoid reading all assignments just to show a version list).
- `ScheduleAssignment` stores `classId`/`teacherId`/`roomId` directly (not just `lessonId`) so the three primary timetable views (by class, by teacher, by room) can each be served by one indexed query on the assignments subcollection, without resolving `Lesson → LessonRequirement → classId` per row.

## 8. Query Patterns

| Query | Collection | Index needed |
|---|---|---|
| List active version's assignments for a class | `versions/{id}/assignments` where `classId == X` | Composite: `classId` |
| List active version's assignments for a teacher | same, `teacherId == X` | Composite: `teacherId` |
| List active version's assignments for a room | same, `roomId == X` | Composite: `roomId` |
| List a school's teachers | `schools/{id}/teachers` | none (collection scan within subcollection is fine at this scale) |
| List a teacher's availability | `schools/{id}/availability` where `ownerType == TEACHER and ownerId == X` | Composite: `ownerType, ownerId` |
| List draft versions for a schedule | `schedules/{id}/versions` where `status == DRAFT` | Single-field (auto) |
| List audit events for an entity | `auditEvents` where `entityType == X and entityId == Y` orderBy `timestamp desc` | Composite: `entityType, entityId, timestamp` |

All composite indexes are declared in `firestore.indexes.json` and checked into the repository (no console-only index configuration).

## 9. Indexes

See §8. Firestore auto-indexes every single field; only compound `where` + `orderBy` combinations above require explicit composite index definitions.

## 10. Security Rules

Deny-by-default; rules mirror (not replace) backend authorization:

```text
match /schools/{schoolId}/{document=**} {
  allow read: if isSignedIn();
  allow write: if false;   // all business writes go through the backend Admin SDK
}

match /schedules/{scheduleId}/{document=**} {
  allow read: if isSignedIn();
  allow write: if false;
}

match /users/{userId} {
  allow read: if request.auth.uid == userId || isAdmin();
  allow write: if false;   // role assignment is backend-managed only
}

match /auditEvents/{eventId} {
  allow read: if isAdmin();
  allow write: if false;
}
```

*Decision:* because all mutating business logic runs through the backend Admin SDK (which bypasses Security Rules), rules here are read-only guards plus a hard `write: if false` — the backend, not Firestore rules, is the authorization source of truth (Architecture §33, master prompt §61). This is intentional and documented, not an oversight.

## 11. Transactions

Firestore transactions (`runTransaction`) are used for:
- `publish()` — updates `ScheduleVersion.status`, `Schedule.activeVersionId`, and archives the previous active version atomically ([04-DESIGN.md](04-DESIGN.md) §21).
- Manual move `applyAssignmentChange()` — reads the target assignment + version's `versionTag`, checks the tag, writes the new assignment and increments `versionTag`, atomically.

Batched writes (`WriteBatch`, non-transactional but atomic) are used for:
- Persisting a full new set of `ScheduleAssignment` documents after generation/rescheduling (potentially hundreds of documents, chunked into batches of ≤500 per Firestore's batch limit).

## 12. Atomic Operations

`versionTag` increments are done via `FieldValue.increment(1)` combined with a transactional precondition check, avoiding read-then-write races on the counter itself.

## 13. Concurrency

*Decision:* optimistic concurrency control via `versionTag` (see [04-DESIGN.md](04-DESIGN.md) §30). Every mutating request against a `ScheduleVersion` includes the `versionTag` it last read; the backend transaction re-reads the current tag and aborts with `ConcurrencyError` (409) if it has changed since. This satisfies NFR-004 (no silent overwrite) without requiring pessimistic locks, which Firestore does not natively support well for this access pattern.

## 14. Data Integrity

- Every write to `versions/{id}/assignments` happens inside the owning version's write path (application layer), never as an ad hoc client write (enforced by rules §10 + backend-only access).
- Referential fields (`teacherId`, `classId`, `roomId`, `requirementId`) are validated for existence by the application layer before persistence (domain validation, [04-DESIGN.md](04-DESIGN.md) §23) — Firestore itself cannot enforce foreign-key integrity.

## 15. Schedule Persistence

One `Schedule` document per school, pointing at the currently active `ScheduleVersion` via `activeVersionId`. All historical/draft versions remain queryable under `schedules/{id}/versions`.

## 16. Schedule Versioning

**Decision — Option C (Hybrid): each `ScheduleVersion` document holds metadata + a denormalized summary; the full assignment set lives in that version's own `assignments` subcollection (a per-version snapshot, not a diff chain).**

Comparison of the three options from the master prompt:

| Option | Description | Verdict |
|---|---|---|
| A — Snapshot-oriented schedule documents | One document per version holding all assignments inline | Rejected — a school with 500+ weekly assignments will exceed or approach Firestore's 1 MiB document limit and forces reading/writing the entire schedule for a single-lesson move. |
| B — Assignment-oriented documents | Assignments as standalone top-level documents referencing a version | Rejected alone — without a version-scoped metadata document, computing a version's score/status/lineage requires an aggregation query every time; also makes "list versions" expensive. |
| **C — Hybrid** | Version metadata document + per-version assignments subcollection | **Selected** — gets B's per-assignment granularity (cheap single-move writes, no document-size ceiling) with A's ease of "read one thing to know the version's status/score," and subcollections naturally scope security rules and indexes per version. |

Each version's assignments are a **full snapshot** (not a diff from the parent), even though most assignments are usually unchanged from the parent version. Reason: diff-chain replay would require walking parent links to materialize a version's full state, which is both slower to read and harder to reason about for the invariant tests in [02-PRD.md](02-PRD.md) §17 (property tests read one version's assignments directly). The storage cost of duplicating unchanged assignments across versions is accepted given Firestore's low storage cost relative to read/compute cost, and is bounded by the retention policy (§"Data Retention" below).

## 17. Assignment Persistence

See §4, §16. `ScheduleAssignment` documents are immutable once their version is `PUBLISHED` or `ARCHIVED` (BR-004); only `DRAFT`-version assignments accept in-place field updates (for manual editing) or additions/removals (during generation/rescheduling before the draft is finalized).

## 18. Availability

Stored as individual `availability` documents (`ownerType`, `ownerId`, `dayId` (optional), `timePeriodId`, `isAvailable`, `preferenceWeight`) rather than an embedded array on `Teacher`/`Class`, so a single availability toggle is a single small document write, and the composite index (`ownerType, ownerId`) supports efficient "all availability for this teacher" reads without touching the Teacher document at all (avoids write contention on a frequently-read Teacher document during frequent availability edits). `dayId` is optional so a school can express both a general "period 3 is generally disliked" rule (no `dayId`) and a specific "...except Tuesday period 3 is fine" override (`dayId` set) — required for SC-002 (teacher preferred *days*, docs/04-DESIGN.md #12), which has no data to read from without day-level granularity.

## 19. Constraints

Hard constraints are **not** persisted as data — they are code (§10–11 of [04-DESIGN.md](04-DESIGN.md)), always active, per the "hard constraints must never be silently bypassed" rule. Soft constraint **weights/parameters** are persisted in `schools/{schoolId}/schedulingConfig/current`:

```json
{
  "softConstraintWeights": {
    "SC-001": 1.0, "SC-002": 1.0, "SC-003": 2.0, "SC-004": 1.5,
    "SC-005": 1.5, "SC-006": 1.0, "SC-007": 0.5, "SC-008": 1.0,
    "SC-009": 3.0, "SC-010": 2.0
  },
  "solver": { "timeoutSeconds": 60, "randomSeed": 42,
              "initialTemperature": 10.0, "coolingRate": 0.995, "minTemperature": 0.01,
              "qualityDecayK": 0.05 }
}
```

`qualityDecayK` is the scoring model's `k` ([04-DESIGN.md](04-DESIGN.md) §13's `quality := 100 * exp(-k * softPenalty / lessonCount)`) — added here alongside the solver's other tunable parameters rather than left with no persisted home.

## 20. Preferences

Represented via `Availability.preferenceWeight`, keyed by owner + optional `dayId` + `timePeriodId` (§4, §18) — not a separate top-level collection, since preferences are always read together with the availability record they annotate. There is no subject-level preference field: none of SC-001..SC-010 needs one (see [04-DESIGN.md](04-DESIGN.md) §2).

## 21. Audit Events

Top-level `auditEvents` collection (§3–4), append-only (`write: if false` in rules, backend-only append via Admin SDK), queried by `entityType`+`entityId` (§8) or by `actor.userId` for a user's activity history. Never updated or deleted (no edit/delete rule exists at all).

## 22. User Data

`users/{userId}` documents (keyed by Firebase Auth UID) hold `{ role: "ADMIN" | "TEACHER", schoolId, teacherId? (if role=TEACHER, links to the Teacher entity), displayName }`. This is the backend's authorization source, resolved on every request from the verified ID token's `uid` (Architecture §23–24) — never trusted from a client-supplied role field.

## 23. School Data

See §3–4. Config subcollections under `schools/{schoolId}`.

## 24. Room Data

See §4 (`rooms` example). `capabilities` is a string array — the only mechanism connecting subjects/lessons to room requirements (no hardcoded room-name logic, master prompt §55).

## 25. Resource Capabilities

`RoomCapability` values are free-form strings validated against a small fixed vocabulary maintained in `schools/{schoolId}` config (e.g., a `capabilityCatalog` field) so the UI can offer a dropdown while still allowing a school to define a new capability without a code change.

## 26. Migration Strategy

Firestore is schemaless, so "migrations" here mean: (a) versioned Pydantic models with backward-compatible optional fields for additive changes, and (b) a documented one-off backend script (`scripts/`) for any breaking field rename/restructure, run against the emulator first, then a staging Firebase project, then production. No automatic schema migration framework is introduced (not justified at this scale).

## 27. Backup Considerations

Firestore's built-in scheduled export-to-GCS-bucket feature is the documented backup mechanism for a production deployment (configuration, not code, deferred to deployment setup — see [03-ARCHITECTURE.md](03-ARCHITECTURE.md) §34). Not required for local development/testing, which uses the emulator (ephemeral by design).

## 28. Data Retention

*Decision:* `ARCHIVED` schedule versions are retained indefinitely by default in MVP (no automatic deletion), since (a) audit/history value is a core product goal (PRD Goal G6) and (b) Firestore storage cost is low relative to the value of full historical traceability for a school-year's worth of versions. A manual admin "purge versions older than X" operation is documented as a Version 2 feature rather than built now, to avoid speculative retention-policy code (master prompt "no premature features").

## 29. Performance

- Reads scoped by subcollection + composite index keep the three primary timetable views (§8) to a single indexed query each, independent of total school size beyond the entities actually shown.
- Writes during generation/rescheduling are chunked into ≤500-document batches (Firestore's batch limit) rather than one write per assignment.
- `Availability` as individual small documents (§18) avoids large-document write amplification from frequent single-slot toggles.

## 30. Firestore Cost Considerations

- Per-document billing model means the assignment-subcollection design (§16) trades more documents for smaller, cheaper, more targeted reads/writes — appropriate given Firestore bills per document read/write, not per byte transferred within reason.
- Denormalized summary fields (§7) exist specifically to avoid N-document reads (and their associated read cost) for common "just show me the list" queries.
- No real-time listeners are used for bulk data in MVP (the frontend polls/fetches via the backend REST API, not direct Firestore snapshot listeners) — avoids unbounded listener-based read costs; revisit only if live-collaboration UX becomes a stated requirement.

## Conceptual ER Diagram

```mermaid
erDiagram
    SCHOOL ||--o{ TEACHER : has
    SCHOOL ||--o{ CLASS : has
    SCHOOL ||--o{ SUBJECT : has
    SCHOOL ||--o{ ROOM : has
    SCHOOL ||--o{ TIME_PERIOD : has
    SCHOOL ||--|| SCHEDULE : owns
    CLASS ||--o{ LESSON_REQUIREMENT : needs
    SUBJECT ||--o{ LESSON_REQUIREMENT : defines
    LESSON_REQUIREMENT ||--o{ LESSON : expands_to
    SCHEDULE ||--o{ SCHEDULE_VERSION : has
    SCHEDULE_VERSION ||--o{ SCHEDULE_ASSIGNMENT : contains
    LESSON ||--o| SCHEDULE_ASSIGNMENT : placed_as
    TEACHER ||--o{ AVAILABILITY : declares
    CLASS ||--o{ AVAILABILITY : declares
    SCHEDULE ||--o{ RESCHEDULING_EVENT : records
    SCHEDULE_ASSIGNMENT }o--|| TEACHER : assigned_to
    SCHEDULE_ASSIGNMENT }o--|| ROOM : uses
```
