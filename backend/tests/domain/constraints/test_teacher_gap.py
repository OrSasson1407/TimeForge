from datetime import time

from app.domain.constraints.teacher_gap import TeacherGapConstraint
from app.domain.models.enums import TimePeriodKind
from app.domain.models.school import TimePeriod
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import ScheduleState

from .conftest import make_candidate


def _periods() -> list[TimePeriod]:
    return [
        TimePeriod(
            id=f"p{i}",
            school_id="s1",
            index=i,
            start_time=time(8 + i, 0),
            end_time=time(8 + i, 45),
            kind=TimePeriodKind.LESSON,
        )
        for i in range(4)
    ]


def test_no_gap_for_consecutive_lessons() -> None:
    constraint = TeacherGapConstraint(weight=1.0, time_periods=_periods())
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id="l1", teacher_id="t1", time_slot=TimeSlot("day_mon", "p0")),
            make_candidate(lesson_id="l2", teacher_id="t1", time_slot=TimeSlot("day_mon", "p1")),
        )
    )

    assert constraint.penalty(state) == 0.0
    assert constraint.explain(state) == []


def test_counts_idle_lesson_periods_between_first_and_last() -> None:
    constraint = TeacherGapConstraint(weight=2.0, time_periods=_periods())
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id="l1", teacher_id="t1", time_slot=TimeSlot("day_mon", "p0")),
            make_candidate(lesson_id="l2", teacher_id="t1", time_slot=TimeSlot("day_mon", "p3")),
        )
    )

    assert constraint.penalty(state) == 2.0  # p1, p2 are idle
    contribution = constraint.explain(state)[0]
    assert contribution.constraint_id == "SC-003"
    assert contribution.raw_penalty == 2.0
    assert contribution.weighted_penalty == 4.0


def test_single_assignment_has_no_gap() -> None:
    constraint = TeacherGapConstraint(weight=1.0, time_periods=_periods())
    state = ScheduleState(
        assignments=(make_candidate(teacher_id="t1", time_slot=TimeSlot("day_mon", "p0")),)
    )

    assert constraint.penalty(state) == 0.0


def test_break_periods_are_not_counted_as_gaps() -> None:
    periods = _periods()
    periods[1] = TimePeriod(
        id="p1",
        school_id="s1",
        index=1,
        start_time=time(9, 0),
        end_time=time(9, 15),
        kind=TimePeriodKind.BREAK,
    )
    constraint = TeacherGapConstraint(weight=1.0, time_periods=periods)
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id="l1", teacher_id="t1", time_slot=TimeSlot("day_mon", "p0")),
            make_candidate(lesson_id="l2", teacher_id="t1", time_slot=TimeSlot("day_mon", "p2")),
        )
    )

    assert constraint.penalty(state) == 0.0  # only a BREAK sits between them
