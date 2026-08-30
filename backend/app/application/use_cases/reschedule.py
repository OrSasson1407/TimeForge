"""RescheduleUseCase (docs/03-ARCHITECTURE.md #26 `POST
/schedules/reschedule`; docs/04-DESIGN.md #17): records the disruption
event, runs `ReschedulingEngine` against the school's currently PUBLISHED
version (BR-001: the published version is "the current timetable" —
rescheduling repairs *that*, never an arbitrary draft), and on a successful
repair persists a new DRAFT `ScheduleVersion` whose parent is the published
one, plus an audit trail entry.

Idempotency mirrors `GenerateScheduleUseCase`: rescheduling runs
synchronously (no background job queue), so a repeated `request_id` replays
the same result rather than repairing twice.
"""

import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.repositories import (
    AuditRepository,
    AvailabilityRepository,
    ClassRepository,
    LessonRequirementRepository,
    ReschedulingEventRepository,
    RoomRepository,
    ScheduleRepository,
    ScheduleVersionRepository,
    SchedulingConfigRepository,
    SchoolDayRepository,
    TeacherRepository,
    TimePeriodRepository,
)
from app.application.use_cases.common import to_candidate_assignment
from app.core.errors import ValidationError
from app.domain.constraints import ConstraintEvaluator, compute_quality
from app.domain.models import (
    Actor,
    AuditEntityType,
    AuditEvent,
    AuditOperation,
    ReschedulingEvent,
    ReschedulingEventType,
    ScheduleScoreSummary,
    ScheduleVersion,
    User,
)
from app.domain.models.value_objects import TimeSlot
from app.domain.rescheduling import (
    DisruptionCost,
    ReschedulingEngine,
    ReschedulingStatus,
    augment_availability_for_event,
    augment_rooms_for_event,
)
from app.domain.scheduling import build_scheduling_problem
from app.domain.scheduling.infeasibility import InfeasibilityResult
from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class RescheduleOutcome:
    status: ReschedulingStatus
    version: ScheduleVersion | None = None
    directly_affected_lesson_ids: tuple[str, ...] = ()
    disruption_cost: DisruptionCost | None = None
    infeasibility: InfeasibilityResult | None = None
    error: str | None = None
    event: ReschedulingEvent | None = None


@dataclass(frozen=True, slots=True)
class RescheduleUseCase:
    schedule_repository: ScheduleRepository
    schedule_version_repository: ScheduleVersionRepository
    rescheduling_event_repository: ReschedulingEventRepository
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
        self,
        school_id: str,
        *,
        request_id: str,
        event_type: ReschedulingEventType,
        target_entity_id: str,
        affected_slots: tuple[TimeSlot, ...],
        reason: str,
        actor: User,
    ) -> RescheduleOutcome:
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
            return RescheduleOutcome(status=ReschedulingStatus.REPAIRED, version=replay)

        if schedule.active_version_id is None:
            raise ValidationError(
                "Cannot report a disruption: no published schedule version exists yet"
            )

        event = ReschedulingEvent(
            id=f"resched_{uuid.uuid4().hex[:16]}",
            schedule_id=schedule.id,
            type=event_type,
            target_entity_id=target_entity_id,
            affected_slots=affected_slots,
            reason=reason,
            reported_at=datetime.now(UTC),
        )
        self.rescheduling_event_repository.append(event)

        published_version_id = schedule.active_version_id
        baseline = tuple(
            to_candidate_assignment(a)
            for a in self.schedule_version_repository.list_assignments(
                schedule.id, published_version_id
            )
        )

        # Built directly (not via the shared `load_scheduling_problem`
        # helper the other use cases use): the raw availability/room lists
        # must be augmented with the disruption BEFORE
        # `build_scheduling_problem` constructs the problem's hard
        # constraints, or the repair search could re-place a lesson right
        # back into the very slot/room that triggered the disruption — see
        # `app.domain.rescheduling.problem_adjustment`'s module docstring.
        config = self.scheduling_config_repository.get(school_id)
        problem = build_scheduling_problem(
            school_id,
            teachers=self.teacher_repository.list(school_id),
            classes=self.class_repository.list(school_id),
            rooms=augment_rooms_for_event(self.room_repository.list(school_id), event),
            requirements=self.requirement_repository.list(school_id),
            availability=augment_availability_for_event(
                self.availability_repository.list_all(school_id), event, school_id=school_id
            ),
            school_days=self.school_day_repository.list(school_id),
            time_periods=self.time_period_repository.list(school_id),
            config=config,
        )
        deadline = time.monotonic() + problem.config.timeout_seconds
        outcome = ReschedulingEngine().reschedule(baseline, event, problem, deadline)

        if outcome.status is not ReschedulingStatus.REPAIRED:
            return RescheduleOutcome(
                status=outcome.status,
                directly_affected_lesson_ids=outcome.directly_affected_lesson_ids,
                infeasibility=outcome.infeasibility,
                error=outcome.error,
                event=event,
            )

        plain_evaluator = ConstraintEvaluator(
            hard_constraints=problem.hard_constraints, soft_constraints=problem.soft_constraints
        )
        score = plain_evaluator.score(ScheduleState(assignments=outcome.assignments))
        quality = (
            compute_quality(
                score.soft_penalty,
                problem.config.quality_decay_k,
                lesson_count=len(problem.lessons),
            )
            if problem.lessons
            else 100.0
        )
        score_summary = ScheduleScoreSummary(
            hard_violations=score.hard_violations, soft_penalty=score.soft_penalty, quality=quality
        )

        version = self.schedule_version_repository.create_draft(
            schedule.id,
            outcome.assignments,
            created_by=actor.id,
            parent_version_id=published_version_id,
            reason=reason,
            score=score_summary,
            request_id=request_id,
        )

        self.audit_repository.append(
            AuditEvent(
                id=f"audit_{uuid.uuid4().hex[:16]}",
                actor=Actor(user_id=actor.id, role=actor.role),
                timestamp=datetime.now(UTC),
                operation=AuditOperation.RESCHEDULED,
                entity_type=AuditEntityType.SCHEDULE_VERSION,
                entity_id=version.id,
                reason=reason,
                after={
                    "movedAssignments": outcome.disruption_cost.moved_assignments
                    if outcome.disruption_cost
                    else 0,
                    "directlyAffectedLessonCount": len(outcome.directly_affected_lesson_ids),
                },
            )
        )

        return RescheduleOutcome(
            status=ReschedulingStatus.REPAIRED,
            version=version,
            directly_affected_lesson_ids=outcome.directly_affected_lesson_ids,
            disruption_cost=outcome.disruption_cost,
            event=event,
        )
