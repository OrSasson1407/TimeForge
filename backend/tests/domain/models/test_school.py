from datetime import time

import pytest

from app.domain.models.enums import TimePeriodKind, Weekday
from app.domain.models.school import Break, School, SchoolDay, TimePeriod


def test_school_valid() -> None:
    school = School(id="s1", name="Northgate High", timezone="Asia/Jerusalem")

    assert school.name == "Northgate High"


def test_school_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name"):
        School(id="s1", name="", timezone="Asia/Jerusalem")


def test_school_rejects_unknown_timezone() -> None:
    with pytest.raises(ValueError, match="timezone"):
        School(id="s1", name="Northgate High", timezone="Not/ARealZone")


def test_school_day_valid() -> None:
    day = SchoolDay(id="d1", school_id="s1", weekday=Weekday.SUNDAY, is_active=True)

    assert day.weekday is Weekday.SUNDAY


def test_time_period_rejects_end_before_start() -> None:
    with pytest.raises(ValueError, match="end_time"):
        TimePeriod(
            id="p1",
            school_id="s1",
            index=0,
            start_time=time(9, 0),
            end_time=time(8, 0),
            kind=TimePeriodKind.LESSON,
        )


def test_time_period_rejects_negative_index() -> None:
    with pytest.raises(ValueError, match="index"):
        TimePeriod(
            id="p1",
            school_id="s1",
            index=-1,
            start_time=time(8, 0),
            end_time=time(8, 45),
            kind=TimePeriodKind.LESSON,
        )


def test_time_period_is_break_reflects_kind() -> None:
    lesson_period = TimePeriod(
        id="p1",
        school_id="s1",
        index=0,
        start_time=time(8, 0),
        end_time=time(8, 45),
        kind=TimePeriodKind.LESSON,
    )
    break_period = TimePeriod(
        id="p2",
        school_id="s1",
        index=1,
        start_time=time(8, 45),
        end_time=time(9, 0),
        kind=TimePeriodKind.BREAK,
    )

    assert lesson_period.is_break is False
    assert break_period.is_break is True


def test_break_rejects_empty_label() -> None:
    with pytest.raises(ValueError, match="label"):
        Break(id="b1", school_id="s1", time_period_id="p2", label="")
