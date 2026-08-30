"""In-memory fake repository implementations (docs/07-CODE_STANDARDS.md
#23: "prefer real, small, fast fakes... over mocking-framework Mock()
objects for repository interfaces"). Used to test application-layer
behavior without needing a live Firestore emulator for every test run —
these fakes are the sanctioned default for fast unit/integration tests
(docs/07-CODE_STANDARDS.md #22, docs/01-CLAUDE.md rule 9); the real
Firestore implementations were separately runtime-verified against a live
emulator in Phase 10 (see
`app/infrastructure/repositories/generic_firestore.py`'s module
docstring).

Each fake conforms to the same Protocol its Firestore counterpart does, so
a test can swap one for the other without touching the code under test.
"""

import dataclasses
import datetime
import uuid
from collections.abc import Iterable

from app.core.errors import ConcurrencyError, ConflictError, NotFoundError, ValidationError
from app.domain.models import (
    AuditEntityType,
    AuditEvent,
    Availability,
    EmailVerification,
    OwnerType,
    ReschedulingEvent,
    Schedule,
    ScheduleAssignment,
    ScheduleScoreSummary,
    ScheduleVersion,
    ScheduleVersionStatus,
    School,
    User,
    UserRole,
)
from app.domain.scheduling import SchedulingConfig
from app.domain.scheduling.candidate import CandidateAssignment


class FakeRepository[T]:
    """Backs every `Repository[T]`-shaped fake (Teacher, Class, Subject,
    Room, SchoolDay, TimePeriod, LessonRequirement)."""

    def __init__(self) -> None:
        self._by_school: dict[str, dict[str, T]] = {}

    def get(self, school_id: str, entity_id: str) -> T | None:
        return self._by_school.get(school_id, {}).get(entity_id)

    def list(self, school_id: str) -> list[T]:
        return list(self._by_school.get(school_id, {}).values())

    def save(self, school_id: str, entity: T) -> None:
        entity_id = entity.id  # type: ignore[attr-defined]
        self._by_school.setdefault(school_id, {})[entity_id] = entity


class FakeSchoolRepository:
    def __init__(self) -> None:
        self._schools: dict[str, School] = {}

    def get(self, school_id: str) -> School | None:
        return self._schools.get(school_id)

    def list(self) -> list[School]:
        return list(self._schools.values())

    def save(self, school: School) -> None:
        self._schools[school.id] = school


class FakeAvailabilityRepository:
    def __init__(self) -> None:
        self._by_school: dict[str, dict[str, Availability]] = {}

    def list_for_owner(
        self, school_id: str, owner_type: OwnerType, owner_id: str
    ) -> list[Availability]:
        return [
            record
            for record in self._by_school.get(school_id, {}).values()
            if record.owner_type is owner_type and record.owner_id == owner_id
        ]

    def list_all(self, school_id: str) -> list[Availability]:
        return list(self._by_school.get(school_id, {}).values())

    def save(self, school_id: str, availability: Availability) -> None:
        self._by_school.setdefault(school_id, {})[availability.id] = availability


class FakeSchedulingConfigRepository:
    def __init__(self) -> None:
        self._by_school: dict[str, SchedulingConfig] = {}

    def get(self, school_id: str) -> SchedulingConfig:
        return self._by_school.get(school_id, SchedulingConfig())

    def save(self, school_id: str, config: SchedulingConfig) -> None:
        self._by_school[school_id] = config


class FakeScheduleRepository:
    def __init__(self) -> None:
        self._schedules: dict[str, Schedule] = {}

    def get(self, school_id: str) -> Schedule | None:
        return self._schedules.get(school_id)

    def get_or_create(self, school_id: str) -> Schedule:
        existing = self._schedules.get(school_id)
        if existing is not None:
            return existing
        created = Schedule(id=school_id, school_id=school_id)
        self._schedules[school_id] = created
        return created

    def _set_active_version(self, school_id: str, version_id: str) -> None:
        schedule = self.get_or_create(school_id)
        self._schedules[school_id] = dataclasses.replace(schedule, active_version_id=version_id)


class FakeScheduleVersionRepository:
    def __init__(self, schedule_repository: FakeScheduleRepository) -> None:
        self._schedule_repository = schedule_repository
        self._versions: dict[tuple[str, str], ScheduleVersion] = {}
        self._assignments: dict[tuple[str, str], dict[str, ScheduleAssignment]] = {}

    def get(self, schedule_id: str, version_id: str) -> ScheduleVersion | None:
        return self._versions.get((schedule_id, version_id))

    def list_versions(self, schedule_id: str) -> list[ScheduleVersion]:
        return [
            version
            for (sched_id, _version_id), version in self._versions.items()
            if sched_id == schedule_id
        ]

    def list_assignments(self, schedule_id: str, version_id: str) -> list[ScheduleAssignment]:
        return list(self._assignments.get((schedule_id, version_id), {}).values())

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
        version_id = f"v_{uuid.uuid4().hex[:12]}"
        persisted = {}
        for candidate in assignments:
            assignment_id = f"a_{uuid.uuid4().hex[:12]}"
            persisted[assignment_id] = ScheduleAssignment(
                id=assignment_id,
                version_id=version_id,
                lesson_id=candidate.lesson_id,
                teacher_id=candidate.teacher_id,
                class_id=candidate.class_id,
                room_id=candidate.room_id,
                time_period_id=candidate.time_slot.time_period_id,
                day_id=candidate.time_slot.day_id,
            )
        self._assignments[(schedule_id, version_id)] = persisted

        version = ScheduleVersion(
            id=version_id,
            schedule_id=schedule_id,
            status=ScheduleVersionStatus.DRAFT,
            created_by=created_by,
            created_at=datetime.datetime.now(datetime.UTC),
            parent_version_id=parent_version_id,
            score=score,
            reason=reason,
            assignment_count=len(persisted),
            version_tag=0,
            request_id=request_id,
        )
        self._versions[(schedule_id, version_id)] = version
        return version

    def apply_assignment_change(
        self,
        schedule_id: str,
        version_id: str,
        updated_assignment: ScheduleAssignment,
        *,
        expected_version_tag: int,
    ) -> None:
        version = self._versions.get((schedule_id, version_id))
        if version is None:
            raise NotFoundError(f"ScheduleVersion {version_id} not found")
        if version.status is not ScheduleVersionStatus.DRAFT:
            raise ConflictError(f"ScheduleVersion {version_id} is not a draft")
        if version.version_tag != expected_version_tag:
            raise ConcurrencyError(
                f"ScheduleVersion {version_id} was modified by someone else "
                f"(expected tag {expected_version_tag}, current {version.version_tag})"
            )

        bucket = self._assignments.setdefault((schedule_id, version_id), {})
        bucket[updated_assignment.id] = updated_assignment
        self._versions[(schedule_id, version_id)] = dataclasses.replace(
            version, version_tag=version.version_tag + 1
        )

    def update_score(self, schedule_id: str, version_id: str, score: ScheduleScoreSummary) -> None:
        version = self._versions.get((schedule_id, version_id))
        if version is None:
            raise NotFoundError(f"ScheduleVersion {version_id} not found")
        self._versions[(schedule_id, version_id)] = dataclasses.replace(version, score=score)

    def publish(self, schedule_id: str, version_id: str, *, expected_version_tag: int) -> None:
        version = self._versions.get((schedule_id, version_id))
        if version is None:
            raise NotFoundError(f"ScheduleVersion {version_id} not found")
        if version.version_tag != expected_version_tag:
            raise ConcurrencyError(
                f"ScheduleVersion {version_id} was modified by someone else "
                f"(expected tag {expected_version_tag}, current {version.version_tag})"
            )
        if not version.is_publishable:
            raise ValidationError(
                f"ScheduleVersion {version_id} cannot be published: not a hard-constraint-clean "
                "draft"
            )

        schedule = self._schedule_repository.get_or_create(schedule_id)
        previous_version_id = schedule.active_version_id
        if previous_version_id is not None:
            previous = self._versions.get((schedule_id, previous_version_id))
            if previous is not None:
                self._versions[(schedule_id, previous_version_id)] = dataclasses.replace(
                    previous, status=ScheduleVersionStatus.ARCHIVED
                )

        self._versions[(schedule_id, version_id)] = dataclasses.replace(
            version, status=ScheduleVersionStatus.PUBLISHED
        )
        self._schedule_repository._set_active_version(schedule_id, version_id)


class FakeAuditRepository:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self._events.append(event)

    def list_for_entity(self, entity_type: AuditEntityType, entity_id: str) -> list[AuditEvent]:
        matches = [
            event
            for event in self._events
            if event.entity_type is entity_type and event.entity_id == entity_id
        ]
        return sorted(matches, key=lambda event: event.timestamp, reverse=True)

    def list_for_actor(self, user_id: str) -> list[AuditEvent]:
        matches = [event for event in self._events if event.actor.user_id == user_id]
        return sorted(matches, key=lambda event: event.timestamp, reverse=True)


class FakeReschedulingEventRepository:
    def __init__(self) -> None:
        self._events: dict[str, list[ReschedulingEvent]] = {}

    def append(self, event: ReschedulingEvent) -> None:
        self._events.setdefault(event.schedule_id, []).append(event)

    def list_for_schedule(self, schedule_id: str) -> list[ReschedulingEvent]:
        return sorted(
            self._events.get(schedule_id, []), key=lambda event: event.reported_at, reverse=True
        )


class FakeUserRepository:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def get(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def list_by_role(self, role: UserRole) -> list[User]:
        return [user for user in self._users.values() if user.role is role]

    def delete(self, user_id: str) -> None:
        self._users.pop(user_id, None)


class FakeVerificationCodeRepository:
    def __init__(self) -> None:
        self._codes: dict[str, EmailVerification] = {}

    def get(self, email: str) -> EmailVerification | None:
        return self._codes.get(email)

    def save(self, verification: EmailVerification) -> None:
        self._codes[verification.email] = verification

    def record_attempt(self, email: str) -> int:
        existing = self._codes.get(email)
        if existing is None:
            return 0
        updated = dataclasses.replace(existing, attempts=existing.attempts + 1)
        self._codes[email] = updated
        return updated.attempts

    def delete(self, email: str) -> None:
        self._codes.pop(email, None)


class FakeEmailSender:
    """Records every call instead of sending anything (docs/07-CODE_STANDARDS.md
    #23) — tests assert against `.sent` rather than a live inbox."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, int]] = []

    def send_verification_code(self, *, to_email: str, code: str, ttl_minutes: int) -> None:
        self.sent.append((to_email, code, ttl_minutes))


class FakeIdentityAdmin:
    """In-memory stand-in for the real Firebase Auth Admin SDK
    (`FirebaseIdentityAdmin`) — the registration/approval flow's only
    dependency on Firebase Auth beyond ID-token verification (which
    `get_current_user` overrides bypass entirely in these tests)."""

    def __init__(self) -> None:
        self._uid_by_email: dict[str, str] = {}
        self._email_by_uid: dict[str, str] = {}
        self.verified_uids: set[str] = set()
        self.disabled_uids: set[str] = set()

    def create_user(self, *, email: str, password: str, display_name: str) -> str:
        del password, display_name
        if email in self._uid_by_email:
            raise ConflictError("An account with this email already exists")
        uid = f"fake_uid_{uuid.uuid4().hex[:12]}"
        self._uid_by_email[email] = uid
        self._email_by_uid[uid] = email
        return uid

    def get_uid_by_email(self, email: str) -> str | None:
        return self._uid_by_email.get(email)

    def get_email(self, uid: str) -> str | None:
        return self._email_by_uid.get(uid)

    def mark_email_verified(self, uid: str) -> None:
        self.verified_uids.add(uid)

    def delete_user(self, uid: str) -> None:
        email = self._email_by_uid.pop(uid, None)
        if email is not None:
            self._uid_by_email.pop(email, None)
        self.verified_uids.discard(uid)

    def set_disabled(self, uid: str, *, disabled: bool) -> None:
        if disabled:
            self.disabled_uids.add(uid)
        else:
            self.disabled_uids.discard(uid)

    def verify_token(self, token: str) -> str:
        """The fake doesn't simulate real token signing/expiry — the token
        string itself IS the uid, which is all these tests need to exercise
        the OAuth-completion endpoint's own logic (docs/07-CODE_STANDARDS.md
        #23)."""
        return token

    def register_known_account(self, *, uid: str, email: str) -> None:
        """Test helper: seeds an email<->uid mapping without going through
        create_user (e.g. to simulate an account that already exists when
        testing duplicate-registration or get_email lookups for a user
        created some other way)."""
        self._uid_by_email[email] = uid
        self._email_by_uid[uid] = email
