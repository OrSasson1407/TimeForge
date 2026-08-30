from typing import ClassVar

from app.domain.models import LessonRequirement
from app.domain.scheduling import Solver
from app.domain.scheduling.result import SolverStatus
from scripts.scenario_factory import small_scenario

from .conftest import build_problem


def test_solver_finds_a_valid_schedule_for_a_simple_problem(
    two_days, three_periods, two_classes, two_teachers, two_rooms
) -> None:
    """PRD §15 Scenario 1: 2 classes, 2 teachers, 2 rooms, no conflicts."""
    requirements = [
        LessonRequirement(
            id="req_c1_math", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=2
        ),
        LessonRequirement(
            id="req_c2_math", school_id="s1", class_id="c2", subject_id="MATH", weekly_periods=2
        ),
    ]
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=requirements,
    )

    result = Solver().solve(problem)

    assert result.status is SolverStatus.VALID
    assert len(result.assignments) == 4
    placed_lesson_ids = {a.lesson_id for a in result.assignments}
    assert placed_lesson_ids == {lesson.id for lesson in problem.lessons}


def test_solver_reports_infeasible_for_a_lab_shortage(
    two_days, three_periods, two_classes, two_teachers, two_rooms
) -> None:
    """PRD §15 Scenario 3: laboratory capacity insufficient -> INFEASIBLE."""
    lab_requirement = LessonRequirement(
        id="req_c1_chem",
        school_id="s1",
        class_id="c1",
        subject_id="CHEM",
        weekly_periods=3,
        required_capability="CHEMISTRY_LAB",
    )
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=[
            t.__class__(
                id=t.id, school_id="s1", name=t.name, email=t.email, subject_ids=frozenset({"CHEM"})
            )
            for t in two_teachers
        ],
        rooms=two_rooms,  # neither room has CHEMISTRY_LAB
        requirements=[lab_requirement],
    )

    result = Solver().solve(problem)

    assert result.status is SolverStatus.INFEASIBLE
    assert result.infeasibility is not None
    assert result.infeasibility.bottlenecks[0].required_capability == "CHEMISTRY_LAB"


def test_solver_times_out_rather_than_hanging() -> None:
    # A 1ms budget can't possibly place 115 lessons (measured at ~0.5-2s
    # uncapped, see scripts/benchmark_scheduling.py) — deterministic,
    # unlike racing a near-zero timeout against wall-clock precision.
    problem = small_scenario(timeout_seconds=0.001).problem

    result = Solver().solve(problem)

    assert result.status is SolverStatus.TIMEOUT


def test_solver_returns_failed_instead_of_raising_on_a_broken_constraint(
    two_days, three_periods, two_classes, two_teachers, two_rooms, math_requirement
) -> None:
    class _BrokenConstraint:
        id: ClassVar[str] = "BROKEN"

        def is_satisfied(self, state, candidate):
            raise RuntimeError("boom")

        def explain_violation(self, state, candidate):
            raise RuntimeError("boom")

        def violations_in(self, state):
            raise RuntimeError("boom")

    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=[math_requirement],
    )
    broken_problem = problem.__class__(
        school_id=problem.school_id,
        lessons=problem.lessons,
        requirements=problem.requirements,
        time_slots=problem.time_slots,
        teachers=problem.teachers,
        classes=problem.classes,
        rooms=problem.rooms,
        availability=problem.availability,
        hard_constraints=(*problem.hard_constraints, _BrokenConstraint()),
        config=problem.config,
    )

    result = Solver().solve(broken_problem)

    assert result.status is SolverStatus.FAILED
    assert result.error is not None and "boom" in result.error
