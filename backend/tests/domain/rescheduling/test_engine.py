"""Integration-level tests for `ReschedulingEngine` (docs/04-DESIGN.md #17):
build a small solvable problem, solve it once to get a baseline, disrupt it,
and verify the repair — this is what proves the disruption-adjustment
mechanism (`problem_adjustment.py`) actually prevents the repair from
re-placing a lesson right back into the slot that was just disrupted, not
just that the pieces compile together.
"""

import time as time_module
from datetime import UTC, datetime, time

from app.domain.constraints import (
    BreakConstraint,
    ClassAvailabilityConstraint,
    ClassConflictConstraint,
    RoomCapabilityConstraint,
    RoomCapacityConstraint,
    RoomConflictConstraint,
    TeacherAvailabilityConstraint,
    TeacherConflictConstraint,
)
from app.domain.models import (
    Class,
    LessonRequirement,
    ReschedulingEventType,
    Room,
    SchoolDay,
    Teacher,
    TimePeriod,
)
from app.domain.models.enums import TimePeriodKind, Weekday
from app.domain.models.rescheduling import ReschedulingEvent
from app.domain.rescheduling.disruption_cost import DisruptionCost
from app.domain.rescheduling.engine import ReschedulingEngine, ReschedulingStatus
from app.domain.rescheduling.problem_adjustment import (
    augment_availability_for_event,
    augment_rooms_for_event,
)
from app.domain.scheduling import SchedulingConfig, SchedulingProblem, Solver, build_time_slots
from app.domain.scheduling.result import SolverStatus

SCHOOL_ID = "s1"
DAY_MON = SchoolDay(id="day_mon", school_id=SCHOOL_ID, weekday=Weekday.MONDAY, is_active=True)
DAY_TUE = SchoolDay(id="day_tue", school_id=SCHOOL_ID, weekday=Weekday.TUESDAY, is_active=True)
PERIOD_1 = TimePeriod(
    id="p1",
    school_id=SCHOOL_ID,
    index=0,
    start_time=time(8, 0),
    end_time=time(8, 45),
    kind=TimePeriodKind.LESSON,
)
PERIOD_2 = TimePeriod(
    id="p2",
    school_id=SCHOOL_ID,
    index=1,
    start_time=time(8, 45),
    end_time=time(9, 30),
    kind=TimePeriodKind.LESSON,
)
CLASS_C1 = Class(id="c1", school_id=SCHOOL_ID, name="7A", grade=7, student_count=20)
ROOM_R1 = Room(id="r1", school_id=SCHOOL_ID, name="Room 1", capacity=30, room_type="STANDARD")
REQUIREMENT = LessonRequirement(
    id="req1", school_id=SCHOOL_ID, class_id="c1", subject_id="MATH", weekly_periods=2
)


def _build_problem(
    *,
    teachers: list[Teacher],
    days: list[SchoolDay],
    periods: list[TimePeriod],
    availability,
    rooms,
) -> SchedulingProblem:
    hard_constraints = (
        TeacherConflictConstraint(),
        ClassConflictConstraint(),
        RoomConflictConstraint(),
        RoomCapabilityConstraint(lessons=[], requirements=[REQUIREMENT], rooms=rooms),
        TeacherAvailabilityConstraint(availability_records=list(availability)),
        ClassAvailabilityConstraint(availability_records=list(availability)),
        BreakConstraint(time_periods=periods),
        RoomCapacityConstraint(classes=[CLASS_C1], rooms=rooms),
    )
    lessons = REQUIREMENT.expand()
    return SchedulingProblem(
        school_id=SCHOOL_ID,
        lessons=tuple(lessons),
        requirements=(REQUIREMENT,),
        time_slots=build_time_slots(days, periods),
        teachers=tuple(teachers),
        classes=(CLASS_C1,),
        rooms=tuple(rooms),
        availability=tuple(availability),
        hard_constraints=hard_constraints,
        config=SchedulingConfig(timeout_seconds=5.0),
    )


def test_reschedule_repairs_around_a_teacher_disruption() -> None:
    teachers = [
        Teacher(
            id="t1",
            school_id=SCHOOL_ID,
            name="T1",
            email="t1@x.com",
            subject_ids=frozenset({"MATH"}),
        ),
        Teacher(
            id="t2",
            school_id=SCHOOL_ID,
            name="T2",
            email="t2@x.com",
            subject_ids=frozenset({"MATH"}),
        ),
    ]
    days = [DAY_MON, DAY_TUE]
    periods = [PERIOD_1, PERIOD_2]
    problem = _build_problem(
        teachers=teachers, days=days, periods=periods, availability=[], rooms=[ROOM_R1]
    )

    baseline_result = Solver().solve(problem)
    assert baseline_result.status is SolverStatus.VALID
    baseline = baseline_result.assignments
    assert len(baseline) == 2

    disrupted = baseline[0]
    event = ReschedulingEvent(
        id="ev1",
        schedule_id=SCHOOL_ID,
        type=ReschedulingEventType.TEACHER_UNAVAILABLE,
        target_entity_id=disrupted.teacher_id,
        affected_slots=(disrupted.time_slot,),
        reason="Sick leave",
        reported_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    adjusted_problem = _build_problem(
        teachers=teachers,
        days=days,
        periods=periods,
        availability=augment_availability_for_event([], event, school_id=SCHOOL_ID),
        rooms=augment_rooms_for_event([ROOM_R1], event),
    )

    outcome = ReschedulingEngine().reschedule(
        baseline, event, adjusted_problem, deadline=time_module.monotonic() + 5.0
    )

    assert outcome.status is ReschedulingStatus.REPAIRED
    assert len(outcome.assignments) == 2
    assert outcome.directly_affected_lesson_ids == (disrupted.lesson_id,)

    repaired_lesson = next(a for a in outcome.assignments if a.lesson_id == disrupted.lesson_id)
    # The repair must not put the affected lesson right back where the
    # disruption said the teacher is unavailable.
    assert not (
        repaired_lesson.teacher_id == disrupted.teacher_id
        and repaired_lesson.time_slot == disrupted.time_slot
    )

    # The OTHER lesson (frozen — not part of the disruption) is untouched.
    other_baseline = next(a for a in baseline if a.lesson_id != disrupted.lesson_id)
    other_repaired = next(a for a in outcome.assignments if a.lesson_id != disrupted.lesson_id)
    assert other_repaired == other_baseline

    # Something had to change for the affected lesson (whether that's the
    # time slot or the teacher depends on which repair the search/optimizer
    # found — with two interchangeable teachers, a same-slot teacher swap
    # is a perfectly valid, even more minimal, repair).
    assert isinstance(outcome.disruption_cost, DisruptionCost)
    assert outcome.disruption_cost.total >= 1


def test_reschedule_reports_unrepairable_when_no_alternative_exists() -> None:
    # One teacher, one room, exactly two slots for two lessons — fully
    # packed. Disrupting the teacher at BOTH slots leaves nowhere for
    # either lesson to go.
    teachers = [
        Teacher(
            id="t1",
            school_id=SCHOOL_ID,
            name="T1",
            email="t1@x.com",
            subject_ids=frozenset({"MATH"}),
        )
    ]
    days = [DAY_MON]
    periods = [PERIOD_1, PERIOD_2]
    problem = _build_problem(
        teachers=teachers, days=days, periods=periods, availability=[], rooms=[ROOM_R1]
    )

    baseline_result = Solver().solve(problem)
    assert baseline_result.status is SolverStatus.VALID
    baseline = baseline_result.assignments
    assert len(baseline) == 2

    all_slots = tuple(a.time_slot for a in baseline)
    event = ReschedulingEvent(
        id="ev1",
        schedule_id=SCHOOL_ID,
        type=ReschedulingEventType.TEACHER_UNAVAILABLE,
        target_entity_id="t1",
        affected_slots=all_slots,
        reason="Sick leave",
        reported_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    adjusted_problem = _build_problem(
        teachers=teachers,
        days=days,
        periods=periods,
        availability=augment_availability_for_event([], event, school_id=SCHOOL_ID),
        rooms=augment_rooms_for_event([ROOM_R1], event),
    )

    outcome = ReschedulingEngine().reschedule(
        baseline, event, adjusted_problem, deadline=time_module.monotonic() + 5.0
    )

    assert outcome.status is ReschedulingStatus.UNREPAIRABLE
    assert outcome.infeasibility is not None
    assert set(outcome.directly_affected_lesson_ids) == {a.lesson_id for a in baseline}


def test_reschedule_is_a_no_op_when_nothing_is_actually_affected() -> None:
    teachers = [
        Teacher(
            id="t1",
            school_id=SCHOOL_ID,
            name="T1",
            email="t1@x.com",
            subject_ids=frozenset({"MATH"}),
        )
    ]
    days = [DAY_MON, DAY_TUE]
    periods = [PERIOD_1, PERIOD_2]
    problem = _build_problem(
        teachers=teachers, days=days, periods=periods, availability=[], rooms=[ROOM_R1]
    )

    baseline_result = Solver().solve(problem)
    assert baseline_result.status is SolverStatus.VALID
    baseline = baseline_result.assignments

    # A teacher who has no assignments at all is "unavailable" for an
    # event, but nothing needs to change.
    event = ReschedulingEvent(
        id="ev1",
        schedule_id=SCHOOL_ID,
        type=ReschedulingEventType.TEACHER_UNAVAILABLE,
        target_entity_id="ghost_teacher",
        affected_slots=(baseline[0].time_slot,),
        reason="Unrelated",
        reported_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    outcome = ReschedulingEngine().reschedule(
        baseline, event, problem, deadline=time_module.monotonic() + 5.0
    )

    assert outcome.status is ReschedulingStatus.REPAIRED
    assert outcome.assignments == baseline
    assert outcome.disruption_cost == DisruptionCost(0, 0, 0, 0.0)
