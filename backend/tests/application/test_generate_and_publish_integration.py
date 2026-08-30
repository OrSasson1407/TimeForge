"""End-to-end: solve a real scenario (Phase 4-5's engine), persist the
result as a Draft version, publish it, and record an audit trail (Phase 6's
repositories) — all against the in-memory fakes. Proves the pieces compose
correctly; the actual `GenerateScheduleUseCase`/`PublishScheduleUseCase`
orchestration classes are Phase 7 (API layer) scope, not built here.
"""

from datetime import UTC, datetime, timedelta

from app.domain.models import (
    Actor,
    AuditEntityType,
    AuditEvent,
    AuditOperation,
    ScheduleScoreSummary,
    UserRole,
)
from app.domain.scheduling import Solver
from app.domain.scheduling.result import SolverStatus
from scripts.scenario_factory import small_scenario
from tests.support.fakes import (
    FakeAuditRepository,
    FakeScheduleRepository,
    FakeScheduleVersionRepository,
)


def test_generate_solve_persist_and_publish_end_to_end() -> None:
    scenario = small_scenario(timeout_seconds=30.0)
    result = Solver().solve(scenario.problem)
    assert result.status is SolverStatus.VALID
    assert result.score is not None

    schedules = FakeScheduleRepository()
    versions = FakeScheduleVersionRepository(schedules)
    audit = FakeAuditRepository()

    schedule = schedules.get_or_create(scenario.school.id)
    assert schedule.active_version_id is None  # nothing published yet

    # Explicit, distinct timestamps: two back-to-back datetime.now(UTC)
    # calls can land in the same clock tick, which would make the
    # "newest first" ordering assertion below flaky rather than meaningful.
    generated_at = datetime.now(UTC)
    published_at = generated_at + timedelta(seconds=1)

    score_summary = ScheduleScoreSummary(
        hard_violations=result.score.hard_violations,
        soft_penalty=result.score.soft_penalty,
        quality=95.0,
    )
    draft = versions.create_draft(
        schedule.id,
        result.assignments,
        created_by="user_dana",
        reason="Initial generation",
        score=score_summary,
    )
    audit.append(
        AuditEvent(
            id="ae1",
            actor=Actor(user_id="user_dana", role=UserRole.ADMIN),
            timestamp=generated_at,
            operation=AuditOperation.SCHEDULE_GENERATED,
            entity_type=AuditEntityType.SCHEDULE_VERSION,
            entity_id=draft.id,
            after={"assignmentCount": draft.assignment_count},
        )
    )

    assert draft.assignment_count == len(scenario.problem.lessons)
    assert len(versions.list_assignments(schedule.id, draft.id)) == len(scenario.problem.lessons)

    versions.publish(schedule.id, draft.id, expected_version_tag=draft.version_tag)
    audit.append(
        AuditEvent(
            id="ae2",
            actor=Actor(user_id="user_dana", role=UserRole.ADMIN),
            timestamp=published_at,
            operation=AuditOperation.SCHEDULE_PUBLISHED,
            entity_type=AuditEntityType.SCHEDULE_VERSION,
            entity_id=draft.id,
        )
    )

    published_schedule = schedules.get(schedule.id)
    assert published_schedule is not None
    assert published_schedule.active_version_id == draft.id

    published_version = versions.get(schedule.id, draft.id)
    assert published_version is not None
    assert published_version.status.value == "PUBLISHED"

    history = audit.list_for_entity(AuditEntityType.SCHEDULE_VERSION, draft.id)
    assert [event.operation for event in history] == [
        AuditOperation.SCHEDULE_PUBLISHED,
        AuditOperation.SCHEDULE_GENERATED,
    ]
