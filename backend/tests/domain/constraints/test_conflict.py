from app.domain.constraints.conflict import (
    ClassConflictConstraint,
    RoomConflictConstraint,
    TeacherConflictConstraint,
)
from app.domain.constraints.violation import Severity
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE, ScheduleState

from .conftest import make_candidate


def test_teacher_conflict_allows_first_placement(slot: TimeSlot) -> None:
    constraint = TeacherConflictConstraint()
    candidate = make_candidate(teacher_id="t1", time_slot=slot)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is True


def test_teacher_conflict_blocks_double_booking(slot: TimeSlot) -> None:
    constraint = TeacherConflictConstraint()
    existing = make_candidate(lesson_id="l1", teacher_id="t1", time_slot=slot)
    state = EMPTY_SCHEDULE_STATE.with_assignment(existing)
    candidate = make_candidate(lesson_id="l2", teacher_id="t1", time_slot=slot)

    assert constraint.is_satisfied(state, candidate) is False
    violation = constraint.explain_violation(state, candidate)
    assert violation.constraint_id == "HC-001"
    assert violation.severity is Severity.ERROR
    assert "l1" in violation.involved_entities


def test_teacher_conflict_allows_revalidating_the_same_lesson_in_place(slot: TimeSlot) -> None:
    constraint = TeacherConflictConstraint()
    existing = make_candidate(lesson_id="l1", teacher_id="t1", time_slot=slot)
    state = EMPTY_SCHEDULE_STATE.with_assignment(existing)

    assert constraint.is_satisfied(state, existing) is True


def test_teacher_conflict_allows_same_teacher_in_different_slots(
    slot: TimeSlot, other_slot: TimeSlot
) -> None:
    constraint = TeacherConflictConstraint()
    existing = make_candidate(lesson_id="l1", teacher_id="t1", time_slot=slot)
    state = EMPTY_SCHEDULE_STATE.with_assignment(existing)
    candidate = make_candidate(lesson_id="l2", teacher_id="t1", time_slot=other_slot)

    assert constraint.is_satisfied(state, candidate) is True


def test_teacher_conflict_violations_in_finds_hand_built_conflicts(slot: TimeSlot) -> None:
    constraint = TeacherConflictConstraint()
    a = make_candidate(lesson_id="l1", teacher_id="t1", time_slot=slot)
    b = make_candidate(lesson_id="l2", teacher_id="t1", time_slot=slot)
    state = ScheduleState(assignments=(a, b))

    violations = constraint.violations_in(state)

    assert len(violations) == 1
    assert set(violations[0].involved_entities) == {"l1", "l2"}


def test_class_conflict_blocks_double_booking(slot: TimeSlot) -> None:
    constraint = ClassConflictConstraint()
    existing = make_candidate(lesson_id="l1", class_id="c1", time_slot=slot)
    state = EMPTY_SCHEDULE_STATE.with_assignment(existing)
    candidate = make_candidate(lesson_id="l2", class_id="c1", time_slot=slot)

    assert constraint.is_satisfied(state, candidate) is False
    assert constraint.explain_violation(state, candidate).constraint_id == "HC-002"


def test_class_conflict_allows_different_classes_same_slot(slot: TimeSlot) -> None:
    constraint = ClassConflictConstraint()
    existing = make_candidate(lesson_id="l1", class_id="c1", time_slot=slot)
    state = EMPTY_SCHEDULE_STATE.with_assignment(existing)
    candidate = make_candidate(lesson_id="l2", class_id="c2", time_slot=slot)

    assert constraint.is_satisfied(state, candidate) is True


def test_room_conflict_blocks_double_booking(slot: TimeSlot) -> None:
    constraint = RoomConflictConstraint()
    existing = make_candidate(lesson_id="l1", room_id="r1", time_slot=slot)
    state = EMPTY_SCHEDULE_STATE.with_assignment(existing)
    candidate = make_candidate(lesson_id="l2", room_id="r1", time_slot=slot)

    assert constraint.is_satisfied(state, candidate) is False
    assert constraint.explain_violation(state, candidate).constraint_id == "HC-003"


def test_room_conflict_allows_different_rooms_same_slot(slot: TimeSlot) -> None:
    constraint = RoomConflictConstraint()
    existing = make_candidate(lesson_id="l1", room_id="r1", time_slot=slot)
    state = EMPTY_SCHEDULE_STATE.with_assignment(existing)
    candidate = make_candidate(lesson_id="l2", room_id="r2", time_slot=slot)

    assert constraint.is_satisfied(state, candidate) is True
