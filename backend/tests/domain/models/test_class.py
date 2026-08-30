import pytest

from app.domain.models.class_ import Class


def _class(**overrides: object) -> Class:
    defaults: dict[str, object] = {
        "id": "c1",
        "school_id": "s1",
        "name": "7A",
        "grade": 7,
        "student_count": 28,
        "home_room_id": "room_101",
    }
    defaults.update(overrides)
    return Class(**defaults)  # type: ignore[arg-type]


def test_class_valid() -> None:
    class_ = _class()

    assert class_.name == "7A"


def test_class_home_room_is_optional() -> None:
    class_ = _class(home_room_id=None)

    assert class_.home_room_id is None


def test_class_rejects_non_positive_student_count() -> None:
    with pytest.raises(ValueError, match="student_count"):
        _class(student_count=0)


def test_class_rejects_negative_grade() -> None:
    with pytest.raises(ValueError, match="grade"):
        _class(grade=-1)
