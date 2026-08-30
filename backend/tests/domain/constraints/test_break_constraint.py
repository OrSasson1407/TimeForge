from app.domain.constraints.break_constraint import BreakConstraint
from app.domain.models.school import TimePeriod
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE, ScheduleState

from .conftest import make_candidate


def test_lesson_period_is_allowed(lesson_period: TimePeriod) -> None:
    constraint = BreakConstraint(time_periods=[lesson_period])
    slot = TimeSlot(day_id="day_mon", time_period_id=lesson_period.id)
    candidate = make_candidate(time_slot=slot)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is True


def test_break_period_is_blocked(break_period: TimePeriod) -> None:
    constraint = BreakConstraint(time_periods=[break_period])
    slot = TimeSlot(day_id="day_mon", time_period_id=break_period.id)
    candidate = make_candidate(time_slot=slot)

    assert constraint.is_satisfied(EMPTY_SCHEDULE_STATE, candidate) is False
    violation = constraint.explain_violation(EMPTY_SCHEDULE_STATE, candidate)
    assert violation.constraint_id == "HC-007"


def test_violations_in_scans_state_for_break_placements(break_period: TimePeriod) -> None:
    constraint = BreakConstraint(time_periods=[break_period])
    slot = TimeSlot(day_id="day_mon", time_period_id=break_period.id)
    state = ScheduleState(assignments=(make_candidate(time_slot=slot),))

    assert len(constraint.violations_in(state)) == 1
