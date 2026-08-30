import pytest

from app.domain.models.subject import Subject


def _subject(**overrides: object) -> Subject:
    defaults: dict[str, object] = {
        "id": "subj1",
        "school_id": "s1",
        "name": "Chemistry",
        "code": "CHEM",
        "required_capability": "CHEMISTRY_LAB",
    }
    defaults.update(overrides)
    return Subject(**defaults)  # type: ignore[arg-type]


def test_subject_valid_defaults() -> None:
    subject = _subject()

    assert subject.max_daily_occurrences == 1
    assert subject.min_spacing_days == 0


def test_subject_required_capability_is_optional() -> None:
    subject = _subject(required_capability=None)

    assert subject.required_capability is None


def test_subject_rejects_non_positive_max_daily_occurrences() -> None:
    with pytest.raises(ValueError, match="max_daily_occurrences"):
        _subject(max_daily_occurrences=0)


def test_subject_rejects_negative_min_spacing_days() -> None:
    with pytest.raises(ValueError, match="min_spacing_days"):
        _subject(min_spacing_days=-1)
