from datetime import UTC, datetime

import pytest

from app.domain.models.enums import ScheduleVersionStatus
from app.domain.models.schedule import (
    Schedule,
    ScheduleAssignment,
    ScheduleScoreSummary,
    ScheduleVersion,
)


def _version(**overrides: object) -> ScheduleVersion:
    defaults: dict[str, object] = {
        "id": "v1",
        "schedule_id": "sch1",
        "status": ScheduleVersionStatus.DRAFT,
        "created_by": "user_dana",
        "created_at": datetime(2026, 2, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return ScheduleVersion(**defaults)  # type: ignore[arg-type]


def test_schedule_starts_without_an_active_version() -> None:
    schedule = Schedule(id="sch1", school_id="s1")

    assert schedule.active_version_id is None


def test_schedule_score_summary_rejects_quality_out_of_range() -> None:
    with pytest.raises(ValueError, match="quality"):
        ScheduleScoreSummary(hard_violations=0, soft_penalty=10.0, quality=0)


def test_schedule_score_summary_rejects_negative_hard_violations() -> None:
    with pytest.raises(ValueError, match="hard_violations"):
        ScheduleScoreSummary(hard_violations=-1, soft_penalty=10.0, quality=80.0)


def test_draft_without_score_is_not_publishable() -> None:
    version = _version()

    assert version.is_publishable is False


def test_draft_with_hard_violations_is_not_publishable() -> None:
    version = _version(
        score=ScheduleScoreSummary(hard_violations=2, soft_penalty=5.0, quality=60.0)
    )

    assert version.is_publishable is False


def test_draft_with_zero_hard_violations_is_publishable() -> None:
    version = _version(
        score=ScheduleScoreSummary(hard_violations=0, soft_penalty=5.0, quality=90.0)
    )

    assert version.is_publishable is True


def test_published_version_is_not_publishable_again() -> None:
    version = _version(
        status=ScheduleVersionStatus.PUBLISHED,
        score=ScheduleScoreSummary(hard_violations=0, soft_penalty=5.0, quality=90.0),
    )

    assert version.is_publishable is False


def test_schedule_assignment_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="room_id"):
        ScheduleAssignment(
            id="a1",
            version_id="v1",
            lesson_id="l1",
            teacher_id="t1",
            class_id="c1",
            room_id="",
            time_period_id="p1",
            day_id="d1",
        )
