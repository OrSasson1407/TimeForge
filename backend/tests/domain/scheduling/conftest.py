from datetime import time

import pytest

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
    Room,
    SchoolDay,
    Teacher,
    TimePeriod,
    TimePeriodKind,
    Weekday,
)
from app.domain.scheduling import SchedulingConfig, SchedulingProblem, build_time_slots


@pytest.fixture
def two_days() -> list[SchoolDay]:
    return [
        SchoolDay(id="day_mon", school_id="s1", weekday=Weekday.MONDAY, is_active=True),
        SchoolDay(id="day_tue", school_id="s1", weekday=Weekday.TUESDAY, is_active=True),
    ]


@pytest.fixture
def three_periods() -> list[TimePeriod]:
    return [
        TimePeriod(
            id="p1",
            school_id="s1",
            index=0,
            start_time=time(8, 0),
            end_time=time(8, 45),
            kind=TimePeriodKind.LESSON,
        ),
        TimePeriod(
            id="p2",
            school_id="s1",
            index=1,
            start_time=time(8, 45),
            end_time=time(9, 0),
            kind=TimePeriodKind.BREAK,
        ),
        TimePeriod(
            id="p3",
            school_id="s1",
            index=2,
            start_time=time(9, 0),
            end_time=time(9, 45),
            kind=TimePeriodKind.LESSON,
        ),
    ]


@pytest.fixture
def two_classes() -> list[Class]:
    return [
        Class(id="c1", school_id="s1", name="7A", grade=7, student_count=25),
        Class(id="c2", school_id="s1", name="7B", grade=7, student_count=25),
    ]


@pytest.fixture
def two_teachers() -> list[Teacher]:
    return [
        Teacher(
            id="t1",
            school_id="s1",
            name="Teacher 1",
            email="t1@example.com",
            subject_ids=frozenset({"MATH"}),
        ),
        Teacher(
            id="t2",
            school_id="s1",
            name="Teacher 2",
            email="t2@example.com",
            subject_ids=frozenset({"MATH"}),
        ),
    ]


@pytest.fixture
def two_rooms() -> list[Room]:
    return [
        Room(id="r1", school_id="s1", name="Room 1", capacity=30, room_type="STANDARD"),
        Room(id="r2", school_id="s1", name="Room 2", capacity=30, room_type="STANDARD"),
    ]


def build_problem(
    *,
    days,
    periods,
    classes,
    teachers,
    rooms,
    requirements,
    availability=(),
    timeout_seconds: float = 5.0,
) -> SchedulingProblem:
    lessons = [lesson for requirement in requirements for lesson in requirement.expand()]
    hard_constraints = (
        TeacherConflictConstraint(),
        ClassConflictConstraint(),
        RoomConflictConstraint(),
        RoomCapabilityConstraint(lessons=lessons, requirements=list(requirements), rooms=rooms),
        TeacherAvailabilityConstraint(availability_records=list(availability)),
        ClassAvailabilityConstraint(availability_records=list(availability)),
        BreakConstraint(time_periods=periods),
        RoomCapacityConstraint(classes=classes, rooms=rooms),
    )
    return SchedulingProblem(
        school_id="s1",
        lessons=tuple(lessons),
        requirements=tuple(requirements),
        time_slots=build_time_slots(days, periods),
        teachers=tuple(teachers),
        classes=tuple(classes),
        rooms=tuple(rooms),
        availability=tuple(availability),
        hard_constraints=hard_constraints,
        config=SchedulingConfig(timeout_seconds=timeout_seconds),
    )


@pytest.fixture
def math_requirement() -> LessonRequirement:
    return LessonRequirement(
        id="req_c1_math", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=2
    )
