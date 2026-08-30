from app.domain.constraints.availability import (
    ClassAvailabilityConstraint,
    TeacherAvailabilityConstraint,
)
from app.domain.models.availability import Availability
from app.domain.models.enums import OwnerType
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE, ScheduleState

from .conftest import make_candidate


def test_teacher_with_no_records_is_available_by_default(slot: TimeSlot) -> None:
    constraint = TeacherAvailabilityConstraint(availability_records=[])
    candidate = make_candidate(teacher_id="t1", time_slot=slot)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is True


def test_teacher_marked_unavailable_is_blocked(slot: TimeSlot) -> None:
    record = Availability(
        id="a1",
        school_id="s1",
        owner_type=OwnerType.TEACHER,
        owner_id="t1",
        time_period_id=slot.time_period_id,
        is_available=False,
    )
    constraint = TeacherAvailabilityConstraint(availability_records=[record])
    candidate = make_candidate(teacher_id="t1", time_slot=slot)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is False
    violation = constraint.explain_violation(EMPTY_SCHEDULE_STATE, candidate)
    assert violation.constraint_id == "HC-005"


def test_teacher_availability_ignores_class_records(slot: TimeSlot) -> None:
    class_record = Availability(
        id="a1",
        school_id="s1",
        owner_type=OwnerType.CLASS,
        owner_id="t1",  # same id, different owner type
        time_period_id=slot.time_period_id,
        is_available=False,
    )
    constraint = TeacherAvailabilityConstraint(availability_records=[class_record])
    candidate = make_candidate(teacher_id="t1", time_slot=slot)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is True


def test_teacher_availability_violations_in_scans_state(slot: TimeSlot) -> None:
    record = Availability(
        id="a1",
        school_id="s1",
        owner_type=OwnerType.TEACHER,
        owner_id="t1",
        time_period_id=slot.time_period_id,
        is_available=False,
    )
    constraint = TeacherAvailabilityConstraint(availability_records=[record])
    state = ScheduleState(assignments=(make_candidate(teacher_id="t1", time_slot=slot),))

    violations = constraint.violations_in(state)

    assert len(violations) == 1


def test_class_with_no_records_is_available_by_default(slot: TimeSlot) -> None:
    constraint = ClassAvailabilityConstraint(availability_records=[])
    candidate = make_candidate(class_id="c1", time_slot=slot)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is True


def test_class_marked_unavailable_is_blocked(slot: TimeSlot) -> None:
    record = Availability(
        id="a1",
        school_id="s1",
        owner_type=OwnerType.CLASS,
        owner_id="c1",
        time_period_id=slot.time_period_id,
        is_available=False,
    )
    constraint = ClassAvailabilityConstraint(availability_records=[record])
    candidate = make_candidate(class_id="c1", time_slot=slot)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is False
    assert constraint.explain_violation(EMPTY_SCHEDULE_STATE, candidate).constraint_id == "HC-006"
