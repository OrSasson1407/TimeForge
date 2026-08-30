"""RescheduleUseCase, against the in-memory fakes (docs/07-CODE_STANDARDS.md
#23) — proves the full orchestration: idempotent replay, the
no-published-version guard, a real repair producing a new DRAFT version
parented on the published one, the disruption event and audit trail both
being recorded, and an UNREPAIRABLE outcome recording the event without
creating a version.
"""

from dataclasses import dataclass
from datetime import time

import pytest

from app.application.use_cases.generate_schedule import GenerateScheduleUseCase
from app.application.use_cases.publish_schedule import PublishScheduleUseCase
from app.application.use_cases.reschedule import RescheduleUseCase
from app.core.errors import ValidationError
from app.domain.models import (
    AuditEntityType,
    AuditOperation,
    Class,
    LessonRequirement,
    ReschedulingEventType,
    Room,
    SchoolDay,
    Teacher,
    TimePeriod,
    TimePeriodKind,
    User,
    UserRole,
    Weekday,
)
from app.domain.models.value_objects import TimeSlot
from app.domain.rescheduling import ReschedulingStatus
from tests.support.fakes import (
    FakeAuditRepository,
    FakeAvailabilityRepository,
    FakeRepository,
    FakeReschedulingEventRepository,
    FakeScheduleRepository,
    FakeScheduleVersionRepository,
    FakeSchedulingConfigRepository,
)

SCHOOL_ID = "s1"
ADMIN = User(id="admin_1", role=UserRole.ADMIN, school_id=SCHOOL_ID, display_name="Dana")


@dataclass
class _Fixtures:
    schedules: FakeScheduleRepository
    versions: FakeScheduleVersionRepository
    rescheduling_events: FakeReschedulingEventRepository
    teachers: FakeRepository
    classes: FakeRepository
    rooms: FakeRepository
    school_days: FakeRepository
    time_periods: FakeRepository
    requirements: FakeRepository
    availability: FakeAvailabilityRepository
    scheduling_config: FakeSchedulingConfigRepository
    audit: FakeAuditRepository


def _build_fixtures(*, num_teachers: int, num_days: int = 2) -> _Fixtures:
    schedules = FakeScheduleRepository()
    fx = _Fixtures(
        schedules=schedules,
        versions=FakeScheduleVersionRepository(schedules),
        rescheduling_events=FakeReschedulingEventRepository(),
        teachers=FakeRepository(),
        classes=FakeRepository(),
        rooms=FakeRepository(),
        school_days=FakeRepository(),
        time_periods=FakeRepository(),
        requirements=FakeRepository(),
        availability=FakeAvailabilityRepository(),
        scheduling_config=FakeSchedulingConfigRepository(),
        audit=FakeAuditRepository(),
    )

    for i in range(1, num_teachers + 1):
        fx.teachers.save(
            SCHOOL_ID,
            Teacher(
                id=f"t{i}",
                school_id=SCHOOL_ID,
                name=f"T{i}",
                email=f"t{i}@x.com",
                subject_ids=frozenset({"MATH"}),
            ),
        )
    fx.classes.save(
        SCHOOL_ID, Class(id="c1", school_id=SCHOOL_ID, name="7A", grade=7, student_count=20)
    )
    fx.rooms.save(
        SCHOOL_ID,
        Room(id="r1", school_id=SCHOOL_ID, name="Room 1", capacity=30, room_type="STANDARD"),
    )
    days = [Weekday.MONDAY, Weekday.TUESDAY, Weekday.WEDNESDAY, Weekday.THURSDAY, Weekday.FRIDAY]
    for weekday in days[:num_days]:
        fx.school_days.save(
            SCHOOL_ID,
            SchoolDay(
                id=f"day_{weekday.value.lower()}",
                school_id=SCHOOL_ID,
                weekday=weekday,
                is_active=True,
            ),
        )
    fx.time_periods.save(
        SCHOOL_ID,
        TimePeriod(
            id="p1",
            school_id=SCHOOL_ID,
            index=0,
            start_time=time(8, 0),
            end_time=time(8, 45),
            kind=TimePeriodKind.LESSON,
        ),
    )
    fx.time_periods.save(
        SCHOOL_ID,
        TimePeriod(
            id="p2",
            school_id=SCHOOL_ID,
            index=1,
            start_time=time(8, 45),
            end_time=time(9, 30),
            kind=TimePeriodKind.LESSON,
        ),
    )
    fx.requirements.save(
        SCHOOL_ID,
        LessonRequirement(
            id="req1", school_id=SCHOOL_ID, class_id="c1", subject_id="MATH", weekly_periods=2
        ),
    )
    return fx


@pytest.fixture
def fixtures() -> _Fixtures:
    return _build_fixtures(num_teachers=2)


def _generate_and_publish(fx: _Fixtures) -> str:
    generate = GenerateScheduleUseCase(
        schedule_repository=fx.schedules,
        schedule_version_repository=fx.versions,
        teacher_repository=fx.teachers,
        class_repository=fx.classes,
        room_repository=fx.rooms,
        requirement_repository=fx.requirements,
        availability_repository=fx.availability,
        school_day_repository=fx.school_days,
        time_period_repository=fx.time_periods,
        scheduling_config_repository=fx.scheduling_config,
        audit_repository=fx.audit,
    )
    outcome = generate.execute(SCHOOL_ID, request_id="gen-1", reason=None, actor=ADMIN)
    assert outcome.version is not None

    publish = PublishScheduleUseCase(
        schedule_version_repository=fx.versions, audit_repository=fx.audit
    )
    publish.execute(SCHOOL_ID, outcome.version.id, expected_version_tag=0, actor=ADMIN)
    return outcome.version.id


def _reschedule_use_case(fx: _Fixtures) -> RescheduleUseCase:
    return RescheduleUseCase(
        schedule_repository=fx.schedules,
        schedule_version_repository=fx.versions,
        rescheduling_event_repository=fx.rescheduling_events,
        teacher_repository=fx.teachers,
        class_repository=fx.classes,
        room_repository=fx.rooms,
        requirement_repository=fx.requirements,
        availability_repository=fx.availability,
        school_day_repository=fx.school_days,
        time_period_repository=fx.time_periods,
        scheduling_config_repository=fx.scheduling_config,
        audit_repository=fx.audit,
    )


def test_reschedule_requires_a_published_version(fixtures: _Fixtures) -> None:
    use_case = _reschedule_use_case(fixtures)

    with pytest.raises(ValidationError, match="published"):
        use_case.execute(
            SCHOOL_ID,
            request_id="req-1",
            event_type=ReschedulingEventType.TEACHER_UNAVAILABLE,
            target_entity_id="t1",
            affected_slots=(TimeSlot(day_id="day_mon", time_period_id="p1"),),
            reason="Sick leave",
            actor=ADMIN,
        )


def test_reschedule_repairs_and_records_event_and_audit(fixtures: _Fixtures) -> None:
    published_version_id = _generate_and_publish(fixtures)
    disrupted = fixtures.versions.list_assignments(SCHOOL_ID, published_version_id)[0]

    use_case = _reschedule_use_case(fixtures)
    outcome = use_case.execute(
        SCHOOL_ID,
        request_id="resched-1",
        event_type=ReschedulingEventType.TEACHER_UNAVAILABLE,
        target_entity_id=disrupted.teacher_id,
        affected_slots=(
            TimeSlot(day_id=disrupted.day_id, time_period_id=disrupted.time_period_id),
        ),
        reason="Sick leave",
        actor=ADMIN,
    )

    assert outcome.status is ReschedulingStatus.REPAIRED
    assert outcome.version is not None
    assert outcome.version.parent_version_id == published_version_id
    assert outcome.version.status.value == "DRAFT"

    # The event was recorded, independent of the repair's success.
    recorded = fixtures.rescheduling_events.list_for_schedule(SCHOOL_ID)
    assert len(recorded) == 1
    assert recorded[0].target_entity_id == disrupted.teacher_id

    # An audit entry exists for the new version.
    audit_events = fixtures.audit.list_for_entity(
        AuditEntityType.SCHEDULE_VERSION, outcome.version.id
    )
    assert any(e.operation is AuditOperation.RESCHEDULED for e in audit_events)


def test_reschedule_replays_idempotently_for_the_same_request_id(fixtures: _Fixtures) -> None:
    published_version_id = _generate_and_publish(fixtures)
    disrupted = fixtures.versions.list_assignments(SCHOOL_ID, published_version_id)[0]
    use_case = _reschedule_use_case(fixtures)
    kwargs = {
        "school_id": SCHOOL_ID,
        "request_id": "resched-1",
        "event_type": ReschedulingEventType.TEACHER_UNAVAILABLE,
        "target_entity_id": disrupted.teacher_id,
        "affected_slots": (
            TimeSlot(day_id=disrupted.day_id, time_period_id=disrupted.time_period_id),
        ),
        "reason": "Sick leave",
        "actor": ADMIN,
    }

    first = use_case.execute(**kwargs)
    second = use_case.execute(**kwargs)

    assert first.version is not None
    assert second.version is not None
    assert first.version.id == second.version.id
    # The second call never re-ran the repair (and never records a second event).
    assert len(fixtures.rescheduling_events.list_for_schedule(SCHOOL_ID)) == 1


def test_reschedule_reports_unrepairable_without_creating_a_version() -> None:
    # Exactly one teacher, one room, two slots for two lessons: the
    # published schedule necessarily uses that one teacher for both slots
    # (there is no other). Disrupting them at both slots leaves nowhere for
    # either lesson to go — no other teacher, no other slot.
    fx = _build_fixtures(num_teachers=1, num_days=1)
    published_version_id = _generate_and_publish(fx)
    assignments = fx.versions.list_assignments(SCHOOL_ID, published_version_id)
    all_slots = tuple(
        TimeSlot(day_id=a.day_id, time_period_id=a.time_period_id) for a in assignments
    )
    assert {a.teacher_id for a in assignments} == {"t1"}

    use_case = _reschedule_use_case(fx)
    outcome = use_case.execute(
        SCHOOL_ID,
        request_id="resched-1",
        event_type=ReschedulingEventType.TEACHER_UNAVAILABLE,
        target_entity_id="t1",
        affected_slots=all_slots,
        reason="Sick leave",
        actor=ADMIN,
    )

    assert outcome.status is ReschedulingStatus.UNREPAIRABLE
    assert outcome.version is None
    assert outcome.infeasibility is not None
    # No new version was created for an unrepairable outcome.
    assert len(fx.versions.list_versions(SCHOOL_ID)) == 1
    # The event was still recorded regardless of the repair outcome.
    assert len(fx.rescheduling_events.list_for_schedule(SCHOOL_ID)) == 1
