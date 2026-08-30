import time
from collections.abc import Sequence

from app.domain.constraints import (
    ConstraintEvaluator,
    HardConstraint,
    HomeRoomPreferenceConstraint,
    TeacherConflictConstraint,
)
from app.domain.models import Class, LessonRequirement, Room, Teacher
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling import SchedulingConfig, SchedulingProblem, SimulatedAnnealingOptimizer
from app.domain.scheduling.candidate import CandidateAssignment
from app.domain.scheduling.state import ScheduleState

SLOT_A = TimeSlot(day_id="day_mon", time_period_id="p1")
SLOT_B = TimeSlot(day_id="day_mon", time_period_id="p2")


def _misplaced_home_room_problem(
    hard_constraints: Sequence[HardConstraint] = (),
) -> tuple[SchedulingProblem, ScheduleState]:
    class_ = Class(
        id="c1", school_id="s1", name="7A", grade=7, student_count=20, home_room_id="r_home"
    )
    teacher = Teacher(
        id="t1", school_id="s1", name="T", email="t@example.com", subject_ids=frozenset({"MATH"})
    )
    home_room = Room(id="r_home", school_id="s1", name="Home", capacity=30, room_type="STANDARD")
    other_room = Room(id="r_other", school_id="s1", name="Other", capacity=30, room_type="STANDARD")
    requirement = LessonRequirement(
        id="req1", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=2
    )
    lessons = requirement.expand()

    home_room_constraint = HomeRoomPreferenceConstraint(
        weight=1.0, classes=[class_], lessons=lessons, requirements=[requirement]
    )
    problem = SchedulingProblem(
        school_id="s1",
        lessons=tuple(lessons),
        requirements=(requirement,),
        time_slots=(SLOT_A, SLOT_B),
        teachers=(teacher,),
        classes=(class_,),
        rooms=(home_room, other_room),
        availability=(),
        hard_constraints=tuple(hard_constraints),
        soft_constraints=(home_room_constraint,),
        config=SchedulingConfig(random_seed=7, initial_temperature=10.0, cooling_rate=0.995),
    )
    # Both lessons are (validly, per hard constraints) placed, but in the
    # WRONG room -> nonzero SC-007 penalty for the optimizer to fix.
    state = ScheduleState(
        assignments=(
            CandidateAssignment(
                lesson_id=lessons[0].id,
                class_id="c1",
                teacher_id="t1",
                room_id="r_other",
                time_slot=SLOT_A,
            ),
            CandidateAssignment(
                lesson_id=lessons[1].id,
                class_id="c1",
                teacher_id="t1",
                room_id="r_other",
                time_slot=SLOT_B,
            ),
        )
    )
    return problem, state


def test_optimizer_reduces_penalty_via_room_reassignment() -> None:
    problem, state = _misplaced_home_room_problem()
    evaluator = ConstraintEvaluator(soft_constraints=problem.soft_constraints)
    initial_penalty = evaluator.score(state).soft_penalty
    assert initial_penalty > 0  # sanity: the scenario really is imperfect

    optimized = SimulatedAnnealingOptimizer().optimize(
        state, problem, evaluator, deadline=time.monotonic() + 2.0
    )

    final_penalty = evaluator.score(optimized).soft_penalty
    assert final_penalty < initial_penalty
    assert evaluator.violations_in(optimized) == []  # never leaves a hard-invalid state


def test_optimizer_never_returns_a_hard_constraint_violation() -> None:
    problem, state = _misplaced_home_room_problem(hard_constraints=(TeacherConflictConstraint(),))
    evaluator = ConstraintEvaluator(
        hard_constraints=problem.hard_constraints, soft_constraints=problem.soft_constraints
    )

    optimized = SimulatedAnnealingOptimizer().optimize(
        state, problem, evaluator, deadline=time.monotonic() + 1.0
    )

    assert evaluator.violations_in(optimized) == []


def test_optimizer_is_a_no_op_for_a_single_assignment() -> None:
    problem, state = _misplaced_home_room_problem()
    single = ScheduleState(assignments=state.assignments[:1])
    evaluator = ConstraintEvaluator(soft_constraints=problem.soft_constraints)

    optimized = SimulatedAnnealingOptimizer().optimize(
        single, problem, evaluator, deadline=time.monotonic() + 1.0
    )

    assert optimized.assignments == single.assignments


def test_optimizer_is_deterministic_given_the_same_seed() -> None:
    problem, state = _misplaced_home_room_problem()
    evaluator = ConstraintEvaluator(soft_constraints=problem.soft_constraints)

    first = SimulatedAnnealingOptimizer().optimize(
        state, problem, evaluator, deadline=time.monotonic() + 1.0
    )
    second = SimulatedAnnealingOptimizer().optimize(
        state, problem, evaluator, deadline=time.monotonic() + 1.0
    )

    assert first.assignments == second.assignments
