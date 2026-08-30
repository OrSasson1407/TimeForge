"""Firestore-backed ScheduleRepository and ScheduleVersionRepository
(docs/05-DATABASE.md #15-17, #11): `publish` and `apply_assignment_change`
each run inside a single Firestore transaction (docs/04-DESIGN.md #21,
#30-31) — Firestore requires every read in a transaction to happen before
any write, which both methods below respect.

Runtime-verified in Phase 10 against a live emulator — see
generic_firestore.py's module docstring. `create_draft` and `publish` were
exercised via real `POST /schedules/generate` and
`POST /schedules/versions/{id}/publish` calls, including `publish`'s
`activeVersionId` update and its BR-005 hard-violations check.
`apply_assignment_change` was exercised both on a valid `expected_version_tag`
(succeeded, `versionTag` incremented) and a stale one (correctly rejected
with a live `409 ConcurrencyError`, not just the fake-repository
equivalent). One nuance live testing did NOT specifically exercise: no
*concurrent* writer was actually simulated, so `@firestore.transactional`'s
`max_attempts` retry-on-ABORT path (as opposed to the deliberate,
never-retried `DomainError` raises below) remains verified only by
reading the client library's documented behavior, not by observation.
"""

from collections.abc import Iterable
from datetime import UTC, datetime

from google.cloud import firestore
from google.cloud.firestore import Client, CollectionReference, DocumentReference

from app.core.errors import ConcurrencyError, ConflictError, NotFoundError, ValidationError
from app.domain.models import (
    Schedule,
    ScheduleAssignment,
    ScheduleScoreSummary,
    ScheduleVersion,
    ScheduleVersionStatus,
)
from app.domain.scheduling.candidate import CandidateAssignment

_FIRESTORE_BATCH_LIMIT = 500


def _version_to_document(version: ScheduleVersion) -> dict[str, object]:
    return {
        "status": version.status.value,
        "parentVersionId": version.parent_version_id,
        "score": (
            {
                "hardViolations": version.score.hard_violations,
                "softPenalty": version.score.soft_penalty,
                "quality": version.score.quality,
            }
            if version.score is not None
            else None
        ),
        "reason": version.reason,
        "assignmentCount": version.assignment_count,
        "versionTag": version.version_tag,
        "createdBy": version.created_by,
        "createdAt": version.created_at,
        "requestId": version.request_id,
    }


def _version_from_document(
    schedule_id: str, doc_id: str, data: dict[str, object]
) -> ScheduleVersion:
    score_data = data.get("score")
    score = None
    if score_data:
        assert isinstance(score_data, dict)
        score = ScheduleScoreSummary(
            hard_violations=int(score_data["hardViolations"]),
            soft_penalty=float(score_data["softPenalty"]),
            quality=float(score_data["quality"]),
        )
    return ScheduleVersion(
        id=doc_id,
        schedule_id=schedule_id,
        status=ScheduleVersionStatus(data["status"]),  # type: ignore[arg-type]
        created_by=str(data["createdBy"]),
        created_at=data["createdAt"],  # type: ignore[arg-type]
        parent_version_id=data.get("parentVersionId"),  # type: ignore[arg-type]
        score=score,
        reason=data.get("reason"),  # type: ignore[arg-type]
        assignment_count=int(data.get("assignmentCount", 0)),  # type: ignore[arg-type]
        version_tag=int(data.get("versionTag", 0)),  # type: ignore[arg-type]
        request_id=data.get("requestId"),  # type: ignore[arg-type]
    )


def _assignment_to_document(assignment: ScheduleAssignment) -> dict[str, object]:
    return {
        "lessonId": assignment.lesson_id,
        "teacherId": assignment.teacher_id,
        "classId": assignment.class_id,
        "roomId": assignment.room_id,
        "timePeriodId": assignment.time_period_id,
        "dayId": assignment.day_id,
    }


def _assignment_from_document(
    version_id: str, doc_id: str, data: dict[str, object]
) -> ScheduleAssignment:
    return ScheduleAssignment(
        id=doc_id,
        version_id=version_id,
        lesson_id=str(data["lessonId"]),
        teacher_id=str(data["teacherId"]),
        class_id=str(data["classId"]),
        room_id=str(data["roomId"]),
        time_period_id=str(data["timePeriodId"]),
        day_id=str(data["dayId"]),
    )


class FirestoreScheduleRepository:
    def __init__(self, client: Client) -> None:
        self._client = client
        self._collection = client.collection("schedules")

    def get(self, school_id: str) -> Schedule | None:
        snapshot = self._collection.document(school_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        return Schedule(
            id=school_id, school_id=school_id, active_version_id=data.get("activeVersionId")
        )

    def get_or_create(self, school_id: str) -> Schedule:
        existing = self.get(school_id)
        if existing is not None:
            return existing
        self._collection.document(school_id).set({"schoolId": school_id, "activeVersionId": None})
        return Schedule(id=school_id, school_id=school_id)


class FirestoreScheduleVersionRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def _schedule_doc(self, schedule_id: str) -> DocumentReference:
        return self._client.collection("schedules").document(schedule_id)

    def _versions_collection(self, schedule_id: str) -> CollectionReference:
        return self._schedule_doc(schedule_id).collection("versions")

    def _assignments_collection(self, schedule_id: str, version_id: str) -> CollectionReference:
        return self._versions_collection(schedule_id).document(version_id).collection("assignments")

    def get(self, schedule_id: str, version_id: str) -> ScheduleVersion | None:
        snapshot = self._versions_collection(schedule_id).document(version_id).get()
        if not snapshot.exists:
            return None
        return _version_from_document(schedule_id, version_id, snapshot.to_dict() or {})

    def list_versions(self, schedule_id: str) -> list[ScheduleVersion]:
        return [
            _version_from_document(schedule_id, doc.id, doc.to_dict() or {})
            for doc in self._versions_collection(schedule_id).stream()
        ]

    def list_assignments(self, schedule_id: str, version_id: str) -> list[ScheduleAssignment]:
        return [
            _assignment_from_document(version_id, doc.id, doc.to_dict() or {})
            for doc in self._assignments_collection(schedule_id, version_id).stream()
        ]

    def create_draft(
        self,
        schedule_id: str,
        assignments: Iterable[CandidateAssignment],
        *,
        created_by: str,
        parent_version_id: str | None = None,
        reason: str | None = None,
        score: ScheduleScoreSummary | None = None,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        candidates = list(assignments)
        version_ref = self._versions_collection(schedule_id).document()
        version = ScheduleVersion(
            id=version_ref.id,
            schedule_id=schedule_id,
            status=ScheduleVersionStatus.DRAFT,
            created_by=created_by,
            created_at=datetime.now(UTC),
            parent_version_id=parent_version_id,
            score=score,
            reason=reason,
            assignment_count=len(candidates),
            version_tag=0,
            request_id=request_id,
        )
        version_ref.set(_version_to_document(version))

        assignments_collection = self._assignments_collection(schedule_id, version_ref.id)
        batch = self._client.batch()
        pending = 0
        for candidate in candidates:
            assignment_ref = assignments_collection.document()
            persisted = ScheduleAssignment(
                id=assignment_ref.id,
                version_id=version_ref.id,
                lesson_id=candidate.lesson_id,
                teacher_id=candidate.teacher_id,
                class_id=candidate.class_id,
                room_id=candidate.room_id,
                time_period_id=candidate.time_slot.time_period_id,
                day_id=candidate.time_slot.day_id,
            )
            batch.set(assignment_ref, _assignment_to_document(persisted))
            pending += 1
            if pending == _FIRESTORE_BATCH_LIMIT:
                batch.commit()
                batch = self._client.batch()
                pending = 0
        if pending:
            batch.commit()

        return version

    def apply_assignment_change(
        self,
        schedule_id: str,
        version_id: str,
        updated_assignment: ScheduleAssignment,
        *,
        expected_version_tag: int,
    ) -> None:
        version_ref = self._versions_collection(schedule_id).document(version_id)
        assignment_ref = self._assignments_collection(schedule_id, version_id).document(
            updated_assignment.id
        )
        transaction = self._client.transaction()

        @firestore.transactional
        def _run(transaction: firestore.Transaction) -> None:
            snapshot = version_ref.get(transaction=transaction)  # read before any write
            if not snapshot.exists:
                raise NotFoundError(f"ScheduleVersion {version_id} not found")
            data = snapshot.to_dict() or {}
            if data.get("status") != ScheduleVersionStatus.DRAFT.value:
                raise ConflictError(f"ScheduleVersion {version_id} is not a draft")
            current_tag = int(data.get("versionTag", 0))
            if current_tag != expected_version_tag:
                raise ConcurrencyError(
                    f"ScheduleVersion {version_id} was modified by someone else "
                    f"(expected tag {expected_version_tag}, current {current_tag})"
                )

            transaction.set(assignment_ref, _assignment_to_document(updated_assignment))
            transaction.update(version_ref, {"versionTag": current_tag + 1})

        _run(transaction)

    def update_score(self, schedule_id: str, version_id: str, score: ScheduleScoreSummary) -> None:
        version_ref = self._versions_collection(schedule_id).document(version_id)
        version_ref.update(
            {
                "score": {
                    "hardViolations": score.hard_violations,
                    "softPenalty": score.soft_penalty,
                    "quality": score.quality,
                }
            }
        )

    def publish(self, schedule_id: str, version_id: str, *, expected_version_tag: int) -> None:
        version_ref = self._versions_collection(schedule_id).document(version_id)
        schedule_ref = self._schedule_doc(schedule_id)
        transaction = self._client.transaction()

        @firestore.transactional
        def _run(transaction: firestore.Transaction) -> None:
            version_snapshot = version_ref.get(transaction=transaction)
            if not version_snapshot.exists:
                raise NotFoundError(f"ScheduleVersion {version_id} not found")
            version_data = version_snapshot.to_dict() or {}
            current_tag = int(version_data.get("versionTag", 0))
            if current_tag != expected_version_tag:
                raise ConcurrencyError(
                    f"ScheduleVersion {version_id} was modified by someone else "
                    f"(expected tag {expected_version_tag}, current {current_tag})"
                )
            score_data = version_data.get("score")
            hard_violations = score_data.get("hardViolations") if score_data else None
            if (
                version_data.get("status") != ScheduleVersionStatus.DRAFT.value
                or hard_violations != 0
            ):
                raise ValidationError(
                    f"ScheduleVersion {version_id} cannot be published: not a hard-constraint-"
                    "clean draft (BR-005)"
                )

            schedule_snapshot = schedule_ref.get(transaction=transaction)  # last read
            previous_version_id = None
            if schedule_snapshot.exists:
                previous_version_id = (schedule_snapshot.to_dict() or {}).get("activeVersionId")

            # From here on: writes only (Firestore transactions require every
            # read to precede every write).
            if previous_version_id and previous_version_id != version_id:
                previous_ref = self._versions_collection(schedule_id).document(previous_version_id)
                transaction.update(previous_ref, {"status": ScheduleVersionStatus.ARCHIVED.value})

            transaction.update(version_ref, {"status": ScheduleVersionStatus.PUBLISHED.value})
            transaction.set(
                schedule_ref, {"schoolId": schedule_id, "activeVersionId": version_id}, merge=True
            )

        _run(transaction)
