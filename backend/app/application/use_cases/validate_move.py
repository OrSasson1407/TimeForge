"""ValidateMoveUseCase (docs/03-ARCHITECTURE.md #26 `POST
/schedules/{id}/versions/{id}/validate-move`): a read-only, side-effect-free
check of a proposed manual move against the same `ConstraintEvaluator` the
solver itself uses (docs/01-CLAUDE.md rule 8) — never a second,
independently-drifting notion of "valid".
"""

from dataclasses import dataclass

from app.application.repositories import (
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
from app.application.use_cases.common import evaluate_proposed_move, load_scheduling_problem
from app.domain.constraints import ConstraintEvaluator, Violation


@dataclass(frozen=True, slots=True)
class MoveValidationResult:
    result: str  # "VALID" | "WARNING" | "INVALID"
    message: str | None
    violation: Violation | None


@dataclass(frozen=True, slots=True)
class ValidateMoveUseCase:
    schedule_version_repository: ScheduleVersionRepository
    teacher_repository: TeacherRepository
    class_repository: ClassRepository
    room_repository: RoomRepository
    requirement_repository: LessonRequirementRepository
    availability_repository: AvailabilityRepository
    school_day_repository: SchoolDayRepository
    time_period_repository: TimePeriodRepository
    scheduling_config_repository: SchedulingConfigRepository

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
    ) -> MoveValidationResult:
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
            return MoveValidationResult(
                result="INVALID",
                message=evaluation.violation.message,
                violation=evaluation.violation,
            )

        assert evaluation.soft_penalty_after is not None  # guaranteed when violation is None
        if evaluation.soft_penalty_after > evaluation.soft_penalty_before:
            delta = evaluation.soft_penalty_after - evaluation.soft_penalty_before
            return MoveValidationResult(
                result="WARNING",
                message=f"This move increases the soft-constraint penalty by {delta:.2f}.",
                violation=None,
            )
        return MoveValidationResult(result="VALID", message=None, violation=None)
