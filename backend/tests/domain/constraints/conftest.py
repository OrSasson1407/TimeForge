from datetime import time

import pytest

from app.domain.models.class_ import Class
from app.domain.models.enums import TimePeriodKind
from app.domain.models.room import Room
from app.domain.models.school import TimePeriod
from app.domain.models.teacher import Teacher
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.candidate import CandidateAssignment

MONDAY = "day_mon"
TUESDAY = "day_tue"


@pytest.fixture
def lesson_period() -> TimePeriod:
    return TimePeriod(
        id="p1",
        school_id="s1",
        index=0,
        start_time=time(8, 0),
        end_time=time(8, 45),
        kind=TimePeriodKind.LESSON,
    )


@pytest.fixture
def break_period() -> TimePeriod:
    return TimePeriod(
        id="p2",
        school_id="s1",
        index=1,
        start_time=time(8, 45),
        end_time=time(9, 0),
        kind=TimePeriodKind.BREAK,
    )


@pytest.fixture
def slot() -> TimeSlot:
    return TimeSlot(day_id=MONDAY, time_period_id="p1")


@pytest.fixture
def other_slot() -> TimeSlot:
    return TimeSlot(day_id=TUESDAY, time_period_id="p1")


@pytest.fixture
def teacher() -> Teacher:
    return Teacher(id="t1", school_id="s1", name="Yossi Cohen", email="yossi@example.com")


@pytest.fixture
def other_teacher() -> Teacher:
    return Teacher(id="t2", school_id="s1", name="Dana Levi", email="dana@example.com")


@pytest.fixture
def class_7a() -> Class:
    return Class(id="c1", school_id="s1", name="7A", grade=7, student_count=28)


@pytest.fixture
def class_7b() -> Class:
    return Class(id="c2", school_id="s1", name="7B", grade=7, student_count=25)


@pytest.fixture
def room() -> Room:
    return Room(id="r1", school_id="s1", name="Room 101", capacity=30, room_type="STANDARD")


@pytest.fixture
def lab_room() -> Room:
    return Room(
        id="r2",
        school_id="s1",
        name="Room 301",
        capacity=30,
        room_type="LABORATORY",
        capabilities=frozenset({"CHEMISTRY_LAB"}),
    )


def make_candidate(
    *,
    lesson_id: str = "l1",
    class_id: str = "c1",
    teacher_id: str = "t1",
    room_id: str = "r1",
    time_slot: TimeSlot,
) -> CandidateAssignment:
    return CandidateAssignment(
        lesson_id=lesson_id,
        class_id=class_id,
        teacher_id=teacher_id,
        room_id=room_id,
        time_slot=time_slot,
    )
