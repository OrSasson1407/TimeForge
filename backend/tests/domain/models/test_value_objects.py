import pytest

from app.domain.models.value_objects import TimeSlot


def test_time_slot_equality_is_by_value() -> None:
    assert TimeSlot(day_id="mon", time_period_id="p1") == TimeSlot(
        day_id="mon", time_period_id="p1"
    )


def test_time_slot_is_hashable_for_use_as_a_dict_key() -> None:
    lookup = {TimeSlot(day_id="mon", time_period_id="p1"): "teacher_123"}

    assert lookup[TimeSlot(day_id="mon", time_period_id="p1")] == "teacher_123"


def test_time_slot_rejects_empty_day_id() -> None:
    with pytest.raises(ValueError, match="day_id"):
        TimeSlot(day_id="", time_period_id="p1")


def test_time_slot_rejects_empty_time_period_id() -> None:
    with pytest.raises(ValueError, match="time_period_id"):
        TimeSlot(day_id="mon", time_period_id="")
