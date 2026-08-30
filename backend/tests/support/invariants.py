"""Shared property/invariant-test helper (docs/02-PRD.md §17 Hard
Constraints, §35 Success Metrics: "0 hard-constraint violations in any
published schedule, measured by the invariant test suite run against every
generated/rescheduled result"; docs/07-CODE_STANDARDS.md §22). One
implementation, reused by the solver's own integration tests
(`tests/domain/scheduling/test_solver_integration.py`) and the
rescheduling engine's (`tests/domain/rescheduling/test_engine_integration.py`)
— generation and repair are held to the exact same bar, checked the exact
same way, via the same `ConstraintEvaluator` the engines themselves use
(docs/01-CLAUDE.md rule 8).
"""

from collections.abc import Sequence

from app.domain.constraints import ConstraintEvaluator
from app.domain.scheduling.candidate import CandidateAssignment
from app.domain.scheduling.problem import SchedulingProblem
from app.domain.scheduling.state import ScheduleState


def assert_no_invariant_violations(
    problem: SchedulingProblem, assignments: Sequence[CandidateAssignment]
) -> None:
    """No teacher/class/room overlap and no other hard-constraint violation
    (HC-001..HC-009), and every lesson in the problem is placed exactly
    once (HC-008: every weekly requirement fully satisfied)."""
    state = ScheduleState(assignments=tuple(assignments))
    evaluator = ConstraintEvaluator(hard_constraints=problem.hard_constraints)
    violations = evaluator.violations_in(state)
    assert violations == [], violations

    placed_lesson_ids = {a.lesson_id for a in assignments}
    expected_lesson_ids = {lesson.id for lesson in problem.lessons}
    assert placed_lesson_ids == expected_lesson_ids
