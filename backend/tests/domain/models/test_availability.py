import math

import pytest

from app.domain.models.availability import Availability, build_availability_index
from app.domain.models.enums import OwnerType


def _availability(**overrides: object) -> Availability:
    defaults: dict[str, object] = {
        "id": "a1",
        "school_id": "s1",
        "owner_type": OwnerType.TEACHER,
        "owner_id": "t1",
        "time_period_id": "p1",
        "is_available": True,
    }
    defaults.update(overrides)
    return Availability(**defaults)  # type: ignore[arg-type]


def test_availability_valid_defaults() -> None:
    availability = _availability()

    assert availability.preference_weight == 0.0


def test_availability_rejects_non_finite_preference_weight() -> None:
    with pytest.raises(ValueError, match="preference_weight"):
        _availability(preference_weight=math.inf)


def test_availability_rejects_empty_owner_id() -> None:
    with pytest.raises(ValueError, match="owner_id"):
        _availability(owner_id="")


def test_availability_can_represent_unavailable_slot() -> None:
    availability = _availability(is_available=False)

    assert availability.is_available is False


def test_availability_rejects_empty_string_day_id() -> None:
    with pytest.raises(ValueError, match="day_id"):
        _availability(day_id="")


def test_availability_day_id_defaults_to_none() -> None:
    assert _availability().day_id is None


def test_index_defaults_to_available_and_neutral_with_no_records() -> None:
    index = build_availability_index([], OwnerType.TEACHER)

    assert index.is_available("t1", "day_mon", "p1") is True
    assert index.preference_weight("t1", "day_mon", "p1") == 0.0


def test_index_day_independent_record_applies_to_every_day() -> None:
    record = _availability(day_id=None, is_available=False, preference_weight=-1.0)
    index = build_availability_index([record], OwnerType.TEACHER)

    assert index.is_available("t1", "day_mon", "p1") is False
    assert index.is_available("t1", "day_tue", "p1") is False


def test_index_day_specific_record_overrides_day_independent_one() -> None:
    general = _availability(id="a1", day_id=None, is_available=False, preference_weight=-1.0)
    specific = _availability(id="a2", day_id="day_tue", is_available=True, preference_weight=1.0)
    index = build_availability_index([general, specific], OwnerType.TEACHER)

    # Monday falls back to the day-independent (unavailable) record...
    assert index.is_available("t1", "day_mon", "p1") is False
    # ...but Tuesday has its own, more specific override.
    assert index.is_available("t1", "day_tue", "p1") is True


def test_index_ignores_records_for_a_different_owner_type() -> None:
    class_record = _availability(owner_type=OwnerType.CLASS, is_available=False)
    index = build_availability_index([class_record], OwnerType.TEACHER)

    assert index.is_available("t1", "day_mon", "p1") is True
