"""ApplyMoveUseCase (docs/03-ARCHITECTURE.md #26 `POST
/schedules/{id}/versions/{id}/apply-move`): re-validates a proposed move
through the exact same check as `ValidateMoveUseCase` (never trusts a
client's earlier `validate-move` call — state may have changed since),
persists it, and immediately recomputes + persists the version's score so
it never goes stale (see `ScheduleVersionRepository.update_score`'s
docstring for why: `publish()`'s BR-005 check trusts the persisted score).
"""

import dataclasses
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.repositories import (
    AuditRepository,
    AvailabilityRepository,
    ClassRepository,
    LessonRequirementRepository,
    RoomRepository,
    ScheduleVersionRepository,
    SchedulingConfigRepository,
    SchoolDayRepository,
    TeacherRepository,
    TimePeriodRepository,
)
from app.application.use_cases.common import (
    evaluate_proposed_move,
    load_scheduling_problem,
    to_candidate_assignment,
)
from app.core.errors import ValidationError
from app.domain.constraints import ConstraintEvaluator, compute_quality
from app.domain.models import (
    Actor,
    AuditEntityType,
    AuditEvent,
    AuditOperation,
    ScheduleAssignment,
    ScheduleScoreSummary,
    User,
)
from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class ApplyMoveUseCase:
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
        self,
        school_id: str,
        schedule_id: str,
        version_id: str,
        *,
        assignment_id: str,
        teacher_id: str,
        room_id: str,
        day_id: str,
        time_period_id: str,
        expected_version_tag: int,
        actor: User,
    ) -> ScheduleAssignment:
        assignments = self.schedule_version_repository.list_assignments(schedule_id, version_id)
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
        evaluator = ConstraintEvaluator(
            hard_constraints=problem.hard_constraints, soft_constraints=problem.soft_constraints
        )
        evaluation = evaluate_proposed_move(
            assignments,
            assignment_id=assignment_id,
            teacher_id=teacher_id,
            room_id=room_id,
            day_id=day_id,
            time_period_id=time_period_id,
            evaluator=evaluator,
        )
        if evaluation.violation is not None:
            raise ValidationError(
                evaluation.violation.message,
                details={"constraintId": evaluation.violation.constraint_id},
            )

        before = evaluation.target
        updated = dataclasses.replace(
            before,
            teacher_id=teacher_id,
            room_id=room_id,
            day_id=day_id,
            time_period_id=time_period_id,
        )
        self.schedule_version_repository.apply_assignment_change(
            schedule_id, version_id, updated, expected_version_tag=expected_version_tag
        )

        after_state = ScheduleState(
            assignments=tuple(
                to_candidate_assignment(updated if a.id == assignment_id else a)
                for a in assignments
            )
        )
        score = evaluator.score(after_state)
        quality = (
            compute_quality(
                score.soft_penalty,
                problem.config.quality_decay_k,
                lesson_count=len(problem.lessons),
            )
            if problem.lessons
            else 100.0
        )
        self.schedule_version_repository.update_score(
            schedule_id,
            version_id,
            ScheduleScoreSummary(
                hard_violations=score.hard_violations,
                soft_penalty=score.soft_penalty,
                quality=quality,
            ),
        )

        self.audit_repository.append(
            AuditEvent(
                id=f"audit_{uuid.uuid4().hex[:16]}",
                actor=Actor(user_id=actor.id, role=actor.role),
                timestamp=datetime.now(UTC),
                operation=AuditOperation.ASSIGNMENT_MOVED,
                entity_type=AuditEntityType.SCHEDULE_ASSIGNMENT,
                entity_id=updated.id,
                before={
                    "teacherId": before.teacher_id,
                    "roomId": before.room_id,
                    "dayId": before.day_id,
                    "timePeriodId": before.time_period_id,
                },
                after={
                    "teacherId": updated.teacher_id,
                    "roomId": updated.room_id,
                    "dayId": updated.day_id,
                    "timePeriodId": updated.time_period_id,
                },
            )
        )

        return updated
