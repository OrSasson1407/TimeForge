from app.domain.constraints.conflict import RoomConflictConstraint, TeacherConflictConstraint
from app.domain.constraints.evaluator import ConstraintEvaluator
from app.domain.constraints.stability import DisruptionMinimizationConstraint
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE, ScheduleState

from .conftest import make_candidate

SLOT = TimeSlot(day_id="day_mon", time_period_id="p1")
OTHER_SLOT = TimeSlot(day_id="day_tue", time_period_id="p1")


def test_empty_evaluator_accepts_everything() -> None:
    evaluator = ConstraintEvaluator()
    candidate = make_candidate(time_slot=SLOT)

    assert evaluator.is_candidate_valid(EMPTY_SCHEDULE_STATE, candidate) is True
    assert evaluator.first_violation(EMPTY_SCHEDULE_STATE, candidate) is None
    assert evaluator.violations_in(EMPTY_SCHEDULE_STATE) == []


def test_is_candidate_valid_false_when_any_constraint_fails() -> None:
    evaluator = ConstraintEvaluator(
        hard_constraints=(TeacherConflictConstraint(), RoomConflictConstraint())
    )
    existing = make_candidate(lesson_id="l1", teacher_id="t1", room_id="r1", time_slot=SLOT)
    state = EMPTY_SCHEDULE_STATE.with_assignment(existing)
    candidate = make_candidate(lesson_id="l2", teacher_id="t1", room_id="r2", time_slot=SLOT)

    assert evaluator.is_candidate_valid(state, candidate) is False


def test_first_violation_returns_the_first_registered_constraints_violation() -> None:
    """Both TeacherConflictConstraint and RoomConflictConstraint would fail
    here; registration order (Teacher first) determines which is reported."""
    evaluator = ConstraintEvaluator(
        hard_constraints=(TeacherConflictConstraint(), RoomConflictConstraint())
    )
    existing = make_candidate(lesson_id="l1", teacher_id="t1", room_id="r1", time_slot=SLOT)
    state = EMPTY_SCHEDULE_STATE.with_assignment(existing)
    candidate = make_candidate(lesson_id="l2", teacher_id="t1", room_id="r1", time_slot=SLOT)

    violation = evaluator.first_violation(state, candidate)

    assert violation is not None
    assert violation.constraint_id == "HC-001"


def test_violations_in_aggregates_across_all_registered_constraints() -> None:
    evaluator = ConstraintEvaluator(
        hard_constraints=(TeacherConflictConstraint(), RoomConflictConstraint())
    )
    a = make_candidate(lesson_id="l1", teacher_id="t1", room_id="r1", time_slot=SLOT)
    b = make_candidate(lesson_id="l2", teacher_id="t1", room_id="r2", time_slot=SLOT)
    state = ScheduleState(assignments=(a, b))

    violations = evaluator.violations_in(state)

    assert {v.constraint_id for v in violations} == {"HC-001"}


def test_valid_candidate_passes_all_registered_constraints() -> None:
    evaluator = ConstraintEvaluator(
        hard_constraints=(TeacherConflictConstraint(), RoomConflictConstraint())
    )
    existing = make_candidate(lesson_id="l1", teacher_id="t1", room_id="r1", time_slot=SLOT)
    state = EMPTY_SCHEDULE_STATE.with_assignment(existing)
    candidate = make_candidate(lesson_id="l2", teacher_id="t2", room_id="r2", time_slot=SLOT)

    assert evaluator.is_candidate_valid(state, candidate) is True


def test_score_with_no_soft_constraints_has_zero_penalty() -> None:
    evaluator = ConstraintEvaluator(hard_constraints=(TeacherConflictConstraint(),))
    state = ScheduleState(assignments=(make_candidate(lesson_id="l1", time_slot=SLOT),))

    score = evaluator.score(state)

    assert score.hard_violations == 0
    assert score.soft_penalty == 0.0
    assert score.breakdown == ()


def test_score_counts_hard_violations_via_the_same_violations_in() -> None:
    evaluator = ConstraintEvaluator(hard_constraints=(TeacherConflictConstraint(),))
    a = make_candidate(lesson_id="l1", teacher_id="t1", time_slot=SLOT)
    b = make_candidate(lesson_id="l2", teacher_id="t1", time_slot=SLOT)
    state = ScheduleState(assignments=(a, b))

    assert evaluator.score(state).hard_violations == 1


def test_score_aggregates_soft_penalty_from_registered_constraints() -> None:
    baseline = (make_candidate(lesson_id="l1", teacher_id="t1", time_slot=SLOT),)
    evaluator = ConstraintEvaluator(
        soft_constraints=(DisruptionMinimizationConstraint(weight=3.0, baseline=baseline),)
    )
    state = ScheduleState(
        assignments=(make_candidate(lesson_id="l1", teacher_id="t1", time_slot=OTHER_SLOT),)
    )

    score = evaluator.score(state)

    assert score.soft_penalty == 3.0
    assert len(score.breakdown) == 1
    assert score.breakdown[0].constraint_id == "SC-009"
