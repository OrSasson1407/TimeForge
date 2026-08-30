from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.candidate import CandidateAssignment
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE, ScheduleState

SLOT = TimeSlot(day_id="day_mon", time_period_id="p1")
OTHER_SLOT = TimeSlot(day_id="day_mon", time_period_id="p2")


def _candidate(**overrides: object) -> CandidateAssignment:
    defaults: dict[str, object] = {
        "lesson_id": "l1",
        "class_id": "c1",
        "teacher_id": "t1",
        "room_id": "r1",
        "time_slot": SLOT,
    }
    defaults.update(overrides)
    return CandidateAssignment(**defaults)  # type: ignore[arg-type]


def test_empty_state_has_no_assignments() -> None:
    assert EMPTY_SCHEDULE_STATE.assignments == ()
    assert EMPTY_SCHEDULE_STATE.teacher_assignment_at("t1", SLOT) is None


def test_with_assignment_returns_a_new_state_leaving_the_original_untouched() -> None:
    candidate = _candidate()

    new_state = EMPTY_SCHEDULE_STATE.with_assignment(candidate)

    assert EMPTY_SCHEDULE_STATE.assignments == ()
    assert new_state.assignments == (candidate,)


def test_indexes_resolve_by_teacher_class_and_room_slot() -> None:
    candidate = _candidate()
    state = EMPTY_SCHEDULE_STATE.with_assignment(candidate)

    assert state.teacher_assignment_at("t1", SLOT) == candidate
    assert state.class_assignment_at("c1", SLOT) == candidate
    assert state.room_assignment_at("r1", SLOT) == candidate
    assert state.teacher_assignment_at("t1", OTHER_SLOT) is None
    assert state.teacher_assignment_at("t2", SLOT) is None


def test_chained_with_assignment_accumulates() -> None:
    first = _candidate(lesson_id="l1", time_slot=SLOT)
    second = _candidate(lesson_id="l2", teacher_id="t2", time_slot=OTHER_SLOT)

    state = EMPTY_SCHEDULE_STATE.with_assignment(first).with_assignment(second)

    assert state.assignments == (first, second)
    assert state.teacher_assignment_at("t2", OTHER_SLOT) == second


def test_state_with_duplicate_slot_keeps_both_in_assignments_list() -> None:
    """The slot index only retains the latest entry per key, but the raw
    assignments list (used by violations_in scans) must keep every entry —
    this is what lets constraints detect conflicts in a hand-built state."""
    first = _candidate(lesson_id="l1", teacher_id="t1", time_slot=SLOT)
    conflicting = _candidate(lesson_id="l2", teacher_id="t1", time_slot=SLOT)

    state = ScheduleState(assignments=(first, conflicting))

    assert state.assignments == (first, conflicting)
