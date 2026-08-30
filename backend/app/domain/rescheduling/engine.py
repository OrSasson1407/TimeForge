"""ReschedulingEngine (docs/04-DESIGN.md #17): "freeze unaffected, repair
the rest" — reuses the exact same search (`run_search`) and optimizer
(`SimulatedAnnealingOptimizer`) the full-generation `Solver` uses, just
seeded with a non-empty starting state and a lesson domain restricted to
the disruption-affected lessons (docs/01-CLAUDE.md rule 8: one
implementation of search, reused everywhere — generation, rescheduling,
and manual-move validation).

Precondition: `problem` must already reflect `event` — built with
`augment_availability_for_event`/`augment_rooms_for_event`
(`problem_adjustment.py`) applied to the raw catalog data BEFORE
`build_scheduling_problem` constructed it. `SchedulingProblem` doesn't
carry the raw `school_days`/`time_periods` needed to rebuild itself from
inside the engine, and patching an already-built problem in place would
leave its hard-constraint instances holding stale (pre-disruption)
availability/room data (see `problem_adjustment.py`'s module docstring) —
so building an already-disruption-aware problem is the caller's job
(`RescheduleUseCase`), not this engine's.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from app.domain.constraints.evaluator import ConstraintEvaluator
from app.domain.constraints.stability import DisruptionMinimizationConstraint
from app.domain.models.rescheduling import ReschedulingEvent
from app.domain.rescheduling.affected import identify_affected_assignments
from app.domain.rescheduling.disruption_cost import DisruptionCost, compute_disruption_cost
from app.domain.scheduling.candidate import CandidateAssignment
from app.domain.scheduling.heuristics import build_lesson_domains, compute_degrees
from app.domain.scheduling.infeasibility import InfeasibilityAnalyzer, InfeasibilityResult
from app.domain.scheduling.optimizer import SimulatedAnnealingOptimizer
from app.domain.scheduling.problem import SchedulingProblem
from app.domain.scheduling.solver import SearchRunStats, run_search
from app.domain.scheduling.state import ScheduleState


class ReschedulingStatus(StrEnum):
    """Mirrors `SolverStatus` (docs/04-DESIGN.md #14) but for a repair run,
    which always starts from an already-valid schedule, so INFEASIBLE
    doesn't apply the same way — a repair that can't be found is
    UNREPAIRABLE (the pre-disruption schedule stays valid, only the
    disruption's own lessons are stuck), not a from-scratch infeasibility."""

    REPAIRED = "REPAIRED"
    UNREPAIRABLE = "UNREPAIRABLE"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ReschedulingOutcome:
    status: ReschedulingStatus
    assignments: tuple[CandidateAssignment, ...] = ()
    directly_affected_lesson_ids: tuple[str, ...] = ()
    disruption_cost: DisruptionCost | None = None
    infeasibility: InfeasibilityResult | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status is ReschedulingStatus.UNREPAIRABLE and self.infeasibility is None:
            raise ValueError(
                "ReschedulingOutcome: UNREPAIRABLE status requires an infeasibility report"
            )
        if self.status is ReschedulingStatus.FAILED and not self.error:
            raise ValueError("ReschedulingOutcome: FAILED status requires an error message")


@dataclass(frozen=True, slots=True)
class ReschedulingEngine:
    """Stateless, like `Solver` — safe to reuse across repair runs."""

    def reschedule(
        self,
        baseline_assignments: Sequence[CandidateAssignment],
        event: ReschedulingEvent,
        problem: SchedulingProblem,
        deadline: float,
    ) -> ReschedulingOutcome:
        try:
            affected = identify_affected_assignments(baseline_assignments, event)
            if not affected:
                return ReschedulingOutcome(
                    status=ReschedulingStatus.REPAIRED,
                    assignments=tuple(baseline_assignments),
                    disruption_cost=DisruptionCost(0, 0, 0, 0.0),
                )

            affected_lesson_ids = {a.lesson_id for a in affected}
            frozen = tuple(
                a for a in baseline_assignments if a.lesson_id not in affected_lesson_ids
            )
            lessons_to_replace = [
                lesson for lesson in problem.lessons if lesson.id in affected_lesson_ids
            ]

            plain_evaluator = ConstraintEvaluator(
                hard_constraints=problem.hard_constraints, soft_constraints=problem.soft_constraints
            )
            search_evaluator = ConstraintEvaluator(
                hard_constraints=problem.hard_constraints,
                soft_constraints=(
                    *problem.soft_constraints,
                    DisruptionMinimizationConstraint(
                        weight=problem.config.soft_constraint_weights.get("SC-009", 1.0),
                        baseline=baseline_assignments,
                    ),
                ),
            )

            initial_state = ScheduleState(assignments=frozen)
            initial_domains = build_lesson_domains(lessons_to_replace, problem)
            degrees = compute_degrees(lessons_to_replace, problem)
            outcome = run_search(
                initial_state,
                initial_domains,
                degrees,
                problem,
                search_evaluator,
                deadline,
                SearchRunStats(),
            )

            if outcome.kind != "success":
                diagnosis = InfeasibilityAnalyzer(problem).analyze(outcome.state)
                if not diagnosis.is_infeasible:
                    diagnosis = InfeasibilityResult(
                        note=(
                            "No repair was found for the affected lessons within the time budget."
                            if outcome.kind == "timeout"
                            else "No repair exists for the affected lessons without violating a "
                            "hard constraint elsewhere in the schedule."
                        )
                    )
                return ReschedulingOutcome(
                    status=ReschedulingStatus.UNREPAIRABLE,
                    directly_affected_lesson_ids=tuple(sorted(affected_lesson_ids)),
                    infeasibility=diagnosis,
                )

            frozen_lesson_ids = frozenset(a.lesson_id for a in frozen)
            optimized = SimulatedAnnealingOptimizer().optimize(
                outcome.state,
                problem,
                search_evaluator,
                deadline,
                frozen_lesson_ids=frozen_lesson_ids,
            )

            cost = compute_disruption_cost(
                baseline_assignments,
                optimized.assignments,
                baseline_soft_penalty=plain_evaluator.score(
                    ScheduleState(assignments=tuple(baseline_assignments))
                ).soft_penalty,
                repaired_soft_penalty=plain_evaluator.score(optimized).soft_penalty,
            )

            return ReschedulingOutcome(
                status=ReschedulingStatus.REPAIRED,
                assignments=optimized.assignments,
                directly_affected_lesson_ids=tuple(sorted(affected_lesson_ids)),
                disruption_cost=cost,
            )
        except Exception as exc:  # noqa: BLE001 -- mirrors Solver.solve(): never raises, see its docstring
            return ReschedulingOutcome(
                status=ReschedulingStatus.FAILED, error=f"{type(exc).__name__}: {exc}"
            )
