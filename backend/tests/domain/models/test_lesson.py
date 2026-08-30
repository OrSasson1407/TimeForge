import pytest

from app.domain.models.lesson import Lesson, LessonRequirement


def _requirement(**overrides: object) -> LessonRequirement:
    defaults: dict[str, object] = {
        "id": "req1",
        "school_id": "s1",
        "class_id": "c1",
        "subject_id": "subj1",
        "weekly_periods": 3,
    }
    defaults.update(overrides)
    return LessonRequirement(**defaults)  # type: ignore[arg-type]


def test_lesson_requirement_rejects_non_positive_weekly_periods() -> None:
    with pytest.raises(ValueError, match="weekly_periods"):
        _requirement(weekly_periods=0)


def test_lesson_requirement_expand_produces_one_lesson_per_weekly_period() -> None:
    requirement = _requirement(weekly_periods=3)

    lessons = requirement.expand()

    assert [lesson.sequence_index for lesson in lessons] == [1, 2, 3]
    assert all(lesson.requirement_id == "req1" for lesson in lessons)
    assert len({lesson.id for lesson in lessons}) == 3  # all ids unique


def test_lesson_rejects_sequence_index_below_one() -> None:
    with pytest.raises(ValueError, match="sequence_index"):
        Lesson(id="l1", requirement_id="req1", sequence_index=0)
