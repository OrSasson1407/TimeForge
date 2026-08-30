"""GenerateScheduleUseCase (docs/03-ARCHITECTURE.md #26 `POST
/schedules/generate`; docs/04-DESIGN.md #"Idempotency"): runs the solver
against a school's current catalog data and persists a new DRAFT
ScheduleVersion.

Idempotency: generation is synchronous in this implementation (no
background job queue exists — the solver runs and returns within the HTTP
request, per the "Fakes only" Phase 6 scope decision to keep the whole
stack framework-light), so the "in-flight duplicate job" race
docs/04-DESIGN.md #"Idempotency" describes cannot occur within one
process. The only realistic duplicate is a client retrying after a dropped
response, which is handled by returning the SAME version instead of
re-solving for an already-seen `request_id`, rather than a `ConflictError`
(there is no in-flight job to conflict with).
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.application.repositories import (
    AuditRepository,
    AvailabilityRepository,
    ClassRepository,
    LessonRequirementRepository,
    RoomRepository,
    ScheduleRepository,
    ScheduleVersionRepository,
    SchedulingConfigRepository,
    SchoolDayRepository,
    TeacherRepository,
    TimePeriodRepository,
)
from app.application.use_cases.common import load_scheduling_problem
from app.domain.constraints import compute_quality
from app.domain.models import (
    Actor,
    AuditEntityType,
    AuditEvent,
    AuditOperation,
    ScheduleScoreSummary,
    ScheduleVersion,
    User,
)
from app.domain.scheduling import Solver
from app.domain.scheduling.infeasibility import InfeasibilityResult
from app.domain.scheduling.result import SearchStats, SolverStatus


@dataclass(frozen=True, slots=True)
class GenerateScheduleOutcome:
    status: SolverStatus
    version: ScheduleVersion | None = None
    infeasibility: InfeasibilityResult | None = None
    error: str | None = None
    stats: SearchStats = field(default_factory=SearchStats)


@dataclass(frozen=True, slots=True)
class GenerateScheduleUseCase:
    schedule_repository: ScheduleRepository
    schedule_version_repository: ScheduleVersionRepository
    teacher_repository: TeacherRepository
    class_repository: ClassRepository
    room_repository: RoomRepository
    requirement_repository: LessonRequirementRepository
    availability_repository: AvailabilityRepository
    school_day_repository: SchoolDayRepository
    time_period_repository: TimePeriodRepository
    scheduling_config_repository: SchedulingConfigRepository
    audit_repository: AuditRepository

    def execute(
        self, school_id: str, *, request_id: str, reason: str | None, actor: User
    ) -> GenerateScheduleOutcome:
        schedule = self.schedule_repository.get_or_create(school_id)

        replay = next(
            (
                version
                for version in self.schedule_version_repository.list_versions(schedule.id)
                if version.request_id == request_id
            ),
            None,
        )
        if replay is not None:
            return GenerateScheduleOutcome(status=SolverStatus.VALID, version=replay)

        problem = load_scheduling_problem(
            school_id,
            teacher_repository=self.teacher_repository,
            class_repository=self.class_repository,
            room_repository=self.room_repository,
            requirement_repository=self.requirement_repository,
            availability_repository=self.availability_repository,
            school_day_repository=self.school_day_repository,
            time_period_repository=self.time_period_repository,
            scheduling_config_repository=self.scheduling_config_repository,
        )
        result = Solver().solve(problem)

        if result.status not in (SolverStatus.VALID, SolverStatus.TIMEOUT):
            return GenerateScheduleOutcome(
                status=result.status,
                infeasibility=result.infeasibility,
                error=result.error,
                stats=result.stats,
            )

        score_summary = None
        if result.score is not None:
            quality = (
                compute_quality(
                    result.score.soft_penalty,
                    problem.config.quality_decay_k,
                    lesson_count=len(problem.lessons),
                )
                if problem.lessons
                else 100.0
            )
            score_summary = ScheduleScoreSummary(
                hard_violations=result.score.hard_violations,
                soft_penalty=result.score.soft_penalty,
                quality=quality,
            )

        version = self.schedule_version_repository.create_draft(
            schedule.id,
            result.assignments,
            created_by=actor.id,
            parent_version_id=schedule.active_version_id,
            reason=reason,
            score=score_summary,
            request_id=request_id,
        )

        self.audit_repository.append(
            AuditEvent(
                id=f"audit_{uuid.uuid4().hex[:16]}",
                actor=Actor(user_id=actor.id, role=actor.role),
                timestamp=datetime.now(UTC),
                operation=AuditOperation.SCHEDULE_GENERATED,
                entity_type=AuditEntityType.SCHEDULE_VERSION,
                entity_id=version.id,
                reason=reason,
            )
        )

        return GenerateScheduleOutcome(
            status=result.status,
            version=version,
            infeasibility=result.infeasibility,
            error=result.error,
            stats=result.stats,
        )
