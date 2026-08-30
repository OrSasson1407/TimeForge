import dataclasses

import pytest

from app.core.errors import ConcurrencyError, NotFoundError, ValidationError
from app.domain.models import ScheduleScoreSummary, ScheduleVersionStatus
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.candidate import CandidateAssignment
from tests.support.fakes import FakeScheduleRepository, FakeScheduleVersionRepository

SLOT = TimeSlot(day_id="day_mon", time_period_id="p1")


def _repos() -> tuple[FakeScheduleRepository, FakeScheduleVersionRepository]:
    schedules = FakeScheduleRepository()
    versions = FakeScheduleVersionRepository(schedules)
    return schedules, versions


def _candidate(**overrides: object) -> CandidateAssignment:
    defaults: dict[str, object] = {
        "lesson_id": "l1",
        "class_id": "c1",
        "teacher_id": "t1",
        "room_id": "r1",
        "time_slot": SLOT,
    }
    defaults.update(overrides)
    return CandidateAssignment(**defaults)  # type: ignore[arg-type]


def test_get_or_create_is_idempotent() -> None:
    schedules, _ = _repos()

    first = schedules.get_or_create("s1")
    second = schedules.get_or_create("s1")

    assert first == second
    assert first.id == "s1"  # Schedule.id == school_id, by decision
    assert first.active_version_id is None


def test_create_draft_mints_ids_and_persists_assignments() -> None:
    schedules, versions = _repos()
    schedule = schedules.get_or_create("s1")

    version = versions.create_draft(
        schedule.id, [_candidate(lesson_id="l1"), _candidate(lesson_id="l2")], created_by="admin"
    )

    assert version.status is ScheduleVersionStatus.DRAFT
    assert version.assignment_count == 2
    assert version.version_tag == 0
    persisted = versions.list_assignments(schedule.id, version.id)
    assert {a.lesson_id for a in persisted} == {"l1", "l2"}
    assert all(a.version_id == version.id for a in persisted)
    assert len({a.id for a in persisted}) == 2  # minted, unique ids


def test_apply_assignment_change_rejects_a_stale_version_tag() -> None:
    schedules, versions = _repos()
    schedule = schedules.get_or_create("s1")
    version = versions.create_draft(schedule.id, [_candidate()], created_by="admin")
    assignment = versions.list_assignments(schedule.id, version.id)[0]
    moved = dataclasses.replace(assignment, room_id="r2")

    with pytest.raises(ConcurrencyError):
        versions.apply_assignment_change(schedule.id, version.id, moved, expected_version_tag=99)


def test_apply_assignment_change_updates_the_assignment_and_bumps_the_tag() -> None:
    schedules, versions = _repos()
    schedule = schedules.get_or_create("s1")
    version = versions.create_draft(schedule.id, [_candidate()], created_by="admin")
    assignment = versions.list_assignments(schedule.id, version.id)[0]
    moved = dataclasses.replace(assignment, room_id="r2")

    versions.apply_assignment_change(
        schedule.id, version.id, moved, expected_version_tag=version.version_tag
    )

    updated = versions.get(schedule.id, version.id)
    assert updated is not None
    assert updated.version_tag == version.version_tag + 1
    persisted = versions.list_assignments(schedule.id, version.id)
    assert persisted[0].room_id == "r2"


def test_publish_requires_zero_hard_violations() -> None:
    schedules, versions = _repos()
    schedule = schedules.get_or_create("s1")
    version = versions.create_draft(
        schedule.id,
        [_candidate()],
        created_by="admin",
        score=ScheduleScoreSummary(hard_violations=1, soft_penalty=0.0, quality=100.0),
    )

    with pytest.raises(ValidationError):
        versions.publish(schedule.id, version.id, expected_version_tag=version.version_tag)


def test_publish_sets_active_version_and_archives_the_previous_one() -> None:
    schedules, versions = _repos()
    schedule = schedules.get_or_create("s1")
    clean_score = ScheduleScoreSummary(hard_violations=0, soft_penalty=0.0, quality=100.0)

    first = versions.create_draft(
        schedule.id, [_candidate()], created_by="admin", score=clean_score
    )
    versions.publish(schedule.id, first.id, expected_version_tag=first.version_tag)

    second = versions.create_draft(
        schedule.id,
        [_candidate()],
        created_by="admin",
        parent_version_id=first.id,
        score=clean_score,
    )
    versions.publish(schedule.id, second.id, expected_version_tag=second.version_tag)

    updated_schedule = schedules.get(schedule.id)
    assert updated_schedule is not None
    assert updated_schedule.active_version_id == second.id
    archived_first = versions.get(schedule.id, first.id)
    assert archived_first is not None
    assert archived_first.status is ScheduleVersionStatus.ARCHIVED
    published_second = versions.get(schedule.id, second.id)
    assert published_second is not None
    assert published_second.status is ScheduleVersionStatus.PUBLISHED


def test_publish_of_unknown_version_raises_not_found() -> None:
    schedules, versions = _repos()
    schedule = schedules.get_or_create("s1")

    with pytest.raises(NotFoundError):
        versions.publish(schedule.id, "nonexistent", expected_version_tag=0)
