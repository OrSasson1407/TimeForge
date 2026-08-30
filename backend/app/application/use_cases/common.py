"""Shared problem-loading and move-evaluation for the scheduling-workflow
use cases (docs/07-CODE_STANDARDS.md #10): every use case that needs to run
the constraint engine (generate, validate-move, apply-move, publish) builds
its `SchedulingProblem` through `load_scheduling_problem`, so "what
constraints apply and how they're wired to data" has exactly one
implementation (docs/01-CLAUDE.md rule 8) shared with
`scripts/scenario_factory.py` via `app.domain.scheduling.build_scheduling_problem`.
`evaluate_proposed_move` is the one place a manual move (validate or apply)
is checked against that same constraint set, so the two endpoints can never
disagree about what "valid" means.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from app.application.repositories import (
    AvailabilityRepository,
    ClassRepository,
    LessonRequirementRepository,
    RoomRepository,
    SchedulingConfigRepository,
    SchoolDayRepository,
    TeacherRepository,
    TimePeriodRepository,
)
from app.core.errors import NotFoundError
from app.domain.constraints import ConstraintEvaluator, Violation
from app.domain.models import ScheduleAssignment
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling import SchedulingProblem, build_scheduling_problem
from app.domain.scheduling.candidate import CandidateAssignment
from app.domain.scheduling.state import ScheduleState


def load_scheduling_problem(
    school_id: str,
    *,
    teacher_repository: TeacherRepository,
    class_repository: ClassRepository,
    room_repository: RoomRepository,
    requirement_repository: LessonRequirementRepository,
    availability_repository: AvailabilityRepository,
    school_day_repository: SchoolDayRepository,
    time_period_repository: TimePeriodRepository,
    scheduling_config_repository: SchedulingConfigRepository,
) -> SchedulingProblem:
    return build_scheduling_problem(
        school_id,
        teachers=teacher_repository.list(school_id),
        classes=class_repository.list(school_id),
        rooms=room_repository.list(school_id),
        requirements=requirement_repository.list(school_id),
        availability=availability_repository.list_all(school_id),
        school_days=school_day_repository.list(school_id),
        time_periods=time_period_repository.list(school_id),
        config=scheduling_config_repository.get(school_id),
    )


def to_candidate_assignment(assignment: ScheduleAssignment) -> CandidateAssignment:
    return CandidateAssignment(
        lesson_id=assignment.lesson_id,
        class_id=assignment.class_id,
        teacher_id=assignment.teacher_id,
        room_id=assignment.room_id,
        time_slot=TimeSlot(day_id=assignment.day_id, time_period_id=assignment.time_period_id),
    )


@dataclass(frozen=True, slots=True)
class MoveEvaluation:
    target: ScheduleAssignment
    candidate: CandidateAssignment
    violation: Violation | None
    soft_penalty_before: float
    #: None when `violation` is set — scoring a state built from an
    #: invalid candidate would be misleading, so it's simply not computed.
    soft_penalty_after: float | None


def evaluate_proposed_move(
    assignments: Sequence[ScheduleAssignment],
    *,
    assignment_id: str,
    teacher_id: str,
    room_id: str,
    day_id: str,
    time_period_id: str,
    evaluator: ConstraintEvaluator,
) -> MoveEvaluation:
    target = next((a for a in assignments if a.id == assignment_id), None)
    if target is None:
        raise NotFoundError(f"ScheduleAssignment {assignment_id} not found")

    others = [a for a in assignments if a.id != assignment_id]
    before_state = ScheduleState(assignments=tuple(to_candidate_assignment(a) for a in assignments))
    state_without_target = ScheduleState(
        assignments=tuple(to_candidate_assignment(a) for a in others)
    )

    candidate = CandidateAssignment(
        lesson_id=target.lesson_id,
        class_id=target.class_id,
        teacher_id=teacher_id,
        room_id=room_id,
        time_slot=TimeSlot(day_id=day_id, time_period_id=time_period_id),
    )

    violation = evaluator.first_violation(state_without_target, candidate)
    soft_penalty_after = None
    if violation is None:
        after_state = state_without_target.with_assignment(candidate)
        soft_penalty_after = evaluator.score(after_state).soft_penalty

    return MoveEvaluation(
        target=target,
        candidate=candidate,
        violation=violation,
        soft_penalty_before=evaluator.score(before_state).soft_penalty,
        soft_penalty_after=soft_penalty_after,
    )
