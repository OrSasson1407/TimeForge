import pytest

from app.domain.models.teacher import Teacher


def _teacher(**overrides: object) -> Teacher:
    defaults: dict[str, object] = {
        "id": "t1",
        "school_id": "s1",
        "name": "Yossi Cohen",
        "email": "yossi@example.com",
        "subject_ids": frozenset({"subj_chem"}),
    }
    defaults.update(overrides)
    return Teacher(**defaults)  # type: ignore[arg-type]


def test_teacher_valid() -> None:
    teacher = _teacher()

    assert teacher.max_weekly_load == 30
    assert teacher.max_consecutive == 4


@pytest.mark.parametrize("email", ["not-an-email", "@example.com", "yossi@"])
def test_teacher_rejects_invalid_email(email: str) -> None:
    with pytest.raises(ValueError, match="email"):
        _teacher(email=email)


def test_teacher_rejects_non_positive_max_weekly_load() -> None:
    with pytest.raises(ValueError, match="max_weekly_load"):
        _teacher(max_weekly_load=0)


def test_teacher_rejects_non_positive_max_consecutive() -> None:
    with pytest.raises(ValueError, match="max_consecutive"):
        _teacher(max_consecutive=0)


def test_teacher_can_teach() -> None:
    teacher = _teacher(subject_ids=frozenset({"subj_chem", "subj_bio"}))

    assert teacher.can_teach("subj_chem") is True
    assert teacher.can_teach("subj_math") is False
