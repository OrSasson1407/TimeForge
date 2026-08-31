"""SimulatedAnnealingOptimizer (docs/04-DESIGN.md #15): improves a
hard-constraint-valid schedule's soft-constraint score within a time
budget, never revisiting an invalid state (every neighbor is re-checked
against the same ConstraintEvaluator used by the search, docs/01-CLAUDE.md
rule 8 — one authoritative rule set, reused again here).

Two neighbor move types, chosen at random each iteration:

- SWAP: exchange two assignments' time slots (each keeps its own
  teacher/room/class). The standard neighborhood for timetabling local
  search, chosen because it tends to preserve feasibility better than an
  arbitrary relocation.
- REASSIGN ROOM: give one assignment a different eligible room. SWAP alone
  never changes any assignment's room (it only exchanges time slots), which
  makes SC-007 (home room preference) and SC-008 (resource utilization) —
  both purely room-dependent — structurally impossible to improve. This
  move exists specifically to make those two constraints optimizable at
  all; without it, roughly a fifth of the registered soft constraints would
  be dead weight regardless of how long annealing ran.

Both move types only ever pick from `movable_indices` — during rescheduling
(`ReschedulingEngine`), the frozen (unaffected) assignments are included in
`state` so the evaluator can score the whole schedule, but must never
actually be changed by a move: `DisruptionMinimizationConstraint` only
*penalizes* touching them, which is a preference signal, not a guarantee,
and simulated annealing can accept a worse-scoring move with nonzero
probability — so "frozen means frozen" has to be enforced structurally
here, not left to the penalty to (probabilistically) discourage. A bug
where a frozen assignment's room changed during a repair was caught by
`tests/domain/rescheduling/test_engine_integration.py` before this
parameter existed.
"""

import dataclasses
import math
import random
import time
from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.constraints.evaluator import ConstraintEvaluator
from app.domain.scheduling.problem import SchedulingProblem
from app.domain.scheduling.state import ScheduleState


def _swap_move(
    state: ScheduleState, rng: random.Random, movable_indices: Sequence[int]
) -> ScheduleState | None:
    if len(movable_indices) < 2:
        return None
    i, j = rng.sample(movable_indices, 2)
    a, b = state.assignments[i], state.assignments[j]
    if a.time_slot == b.time_slot:
        return None  # not a real move

    new_assignments = list(state.assignments)
    new_assignments[i] = dataclasses.replace(a, time_slot=b.time_slot)
    new_assignments[j] = dataclasses.replace(b, time_slot=a.time_slot)
    return ScheduleState(assignments=tuple(new_assignments))


def _reassign_room_move(
    state: ScheduleState,
    problem: SchedulingProblem,
    rng: random.Random,
    movable_indices: Sequence[int],
) -> ScheduleState | None:
    if not movable_indices:
        return None
    i = rng.choice(movable_indices)
    assignment = state.assignments[i]

    lesson = problem.lesson_by_id.get(assignment.lesson_id)
    class_ = problem.class_by_id.get(assignment.class_id)
    if lesson is None or class_ is None:
        return None
    requirement = problem.requirement_by_id.get(lesson.requirement_id)
    if requirement is None:
        return None

    alternatives = [
        room
        for room in problem.eligible_rooms_for(requirement, class_)
        if room.id != assignment.room_id
    ]
    if not alternatives:
        return None

    new_assignments = list(state.assignments)
    new_assignments[i] = dataclasses.replace(assignment, room_id=rng.choice(alternatives).id)
    return ScheduleState(assignments=tuple(new_assignments))


@dataclass(frozen=True, slots=True)
class SimulatedAnnealingOptimizer:
    """Stateless, like Solver — all per-run state is local to `optimize()`."""

    def optimize(
        self,
        state: ScheduleState,
        problem: SchedulingProblem,
        evaluator: ConstraintEvaluator,
        deadline: float,
        *,
        frozen_lesson_ids: frozenset[str] = frozenset(),
    ) -> ScheduleState:
        """`frozen_lesson_ids` are scored (they affect soft-constraint
        context, e.g. gap/conflict-adjacent penalties) but never selected as
        a move's target — empty by default, matching full generation, where
        nothing is frozen. Positions in `state.assignments` map to a fixed
        lesson identity for the whole run (neither move type ever changes
        *which* lesson occupies a given index, only its time slot or room),
        so precomputing the movable index list once up front is valid for
        every iteration below."""
        movable_indices = [
            i for i, a in enumerate(state.assignments) if a.lesson_id not in frozen_lesson_ids
        ]
        if len(movable_indices) < 2:
            return state

        rng = random.Random(problem.config.random_seed)  # noqa: S311 -- seeded for NFR-007 determinism, not crypto
        current = state
        current_penalty = evaluator.soft_penalty(current)
        temperature = problem.config.initial_temperature

        while temperature > problem.config.min_temperature and time.monotonic() < deadline:
            candidate_state = (
                _swap_move(current, rng, movable_indices)
                if rng.random() < 0.5
                else _reassign_room_move(current, problem, rng, movable_indices)
            )
            if candidate_state is None or evaluator.violations_in(candidate_state):
                temperature *= problem.config.cooling_rate
                continue

            candidate_penalty = evaluator.soft_penalty(candidate_state)
            delta = candidate_penalty - current_penalty
            if delta < 0 or rng.random() < math.exp(-delta / temperature):
                current, current_penalty = candidate_state, candidate_penalty
            temperature *= problem.config.cooling_rate

        return current
