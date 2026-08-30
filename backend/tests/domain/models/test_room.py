import pytest

from app.domain.models.enums import RoomStatus
from app.domain.models.room import Room


def _room(**overrides: object) -> Room:
    defaults: dict[str, object] = {
        "id": "r1",
        "school_id": "s1",
        "name": "Room 301",
        "capacity": 35,
        "room_type": "LABORATORY",
        "capabilities": frozenset({"CHEMISTRY_LAB", "PROJECTOR"}),
    }
    defaults.update(overrides)
    return Room(**defaults)  # type: ignore[arg-type]


def test_room_valid_defaults_to_active() -> None:
    room = _room()

    assert room.status is RoomStatus.ACTIVE


def test_room_rejects_non_positive_capacity() -> None:
    with pytest.raises(ValueError, match="capacity"):
        _room(capacity=0)


def test_room_rejects_empty_type() -> None:
    with pytest.raises(ValueError, match="room_type"):
        _room(room_type="")


def test_room_has_capability() -> None:
    room = _room()

    assert room.has_capability("CHEMISTRY_LAB") is True
    assert room.has_capability("GYM") is False


def test_room_can_seat() -> None:
    room = _room(capacity=30)

    assert room.can_seat(30) is True
    assert room.can_seat(31) is False
