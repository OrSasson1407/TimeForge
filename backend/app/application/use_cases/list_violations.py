"""ListViolationsUseCase (docs/03-ARCHITECTURE.md #26 extension): a
read-only, full-state scan of every hard-constraint violation currently
present in a schedule version, reusing the exact same `ConstraintEvaluator`
as generation/validate-move/apply-move (docs/01-CLAUDE.md rule 8) — the
backend half of persistent whole-grid conflict highlighting. The frontend
never computes "is this cell in conflict" itself; it only renders what
this scan reports.
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
from app.application.use_cases.common import load_scheduling_problem, to_candidate_assignment
from app.domain.constraints import ConstraintEvaluator, Violation
from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class ListViolationsUseCase:
    schedule_version_repository: ScheduleVersionRepository
    teacher_repository: TeacherRepository
    class_repository: ClassRepository
    room_repository: RoomRepository
    requirement_repository: LessonRequirementRepository
    availability_repository: AvailabilityRepository
    school_day_repository: SchoolDayRepository
    time_period_repository: TimePeriodRepository
    scheduling_config_repository: SchedulingConfigRepository

    def execute(self, school_id: str, schedule_id: str, version_id: str) -> list[Violation]:
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
        state = ScheduleState(assignments=tuple(to_candidate_assignment(a) for a in assignments))
        return evaluator.violations_in(state)
