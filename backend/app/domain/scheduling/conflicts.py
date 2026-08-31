"""Conflict-set analysis for conflict-directed backjumping (CBJ).

Chronological backtracking undoes the *most recent* decision when a lesson
can't be placed — even when that decision had nothing to do with the
failure. The classic pathological case in timetabling: lesson Z fails
because of a room clash with lesson A placed twenty steps ago; chronological
backtracking then re-tries every one of the nineteen irrelevant decisions in
between, each of which fails for the same untouched reason, before finally
reaching A. CBJ instead asks "who actually blocked me?" and jumps straight
back to the deepest decision in that set (Dechter, *Constraint Processing*
§6; Prosser 1993).

This module answers the "who actually blocked me?" half — `run_search` in
`solver.py` does the jumping.

Correctness note: a conflict set may over-approximate (naming a lesson that
was not strictly necessary to explain the failure) without losing any
solution — the search just jumps less far and degrades toward chronological
backtracking. It must never UNDER-approximate: omitting a genuine culprit
could jump past the decision that needed revisiting and miss a solution. So
every helper below deliberately returns a superset when the precise
minimal explanation is not cheaply available, and `EVERY_ASSIGNMENT` exists
as the always-safe fallback.
"""

from collections.abc import Sequence

from app.domain.models.lesson import Lesson
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.problem import SchedulingProblem
from app.domain.scheduling.state import ScheduleState


def every_assigned_lesson_id(state: ScheduleState) -> frozenset[str]:
    """The always-safe conflict set: "any earlier decision might be to
    blame". Makes CBJ behave exactly like chronological backtracking, which
    is the correct thing to fall back to whenever a failure's real cause
    can't be attributed."""
    return frozenset(assignment.lesson_id for assignment in state.assignments)


def blocking_lesson_ids(
    lesson: Lesson, slot: TimeSlot, state: ScheduleState, problem: SchedulingProblem
) -> frozenset[str]:
    """Which already-placed lessons prevented `lesson` from taking `slot`.

    Mirrors `SchedulingProblem.resolve_placement`'s decision structure, so
    the two can't disagree about why a placement failed:

    - the class is already busy in this slot -> that one lesson is a
      complete explanation on its own;
    - otherwise every eligible teacher was either statically unavailable
      (an availability record, not a placement decision — nothing to blame
      and nothing a backjump could fix) or already teaching, and every
      eligible room was already in use. Each occupying lesson is named.

    An empty result therefore means something real: the slot is unusable
    for reasons no earlier placement caused (no eligible teacher is ever
    available then, no eligible room exists at all), so backjumping past
    this lesson cannot help.
    """
    requirement = problem.requirement_by_id[lesson.requirement_id]
    class_ = problem.class_by_id.get(requirement.class_id)
    if class_ is None:
        return frozenset()

    occupying_class = state.class_assignment_at(class_.id, slot)
    if occupying_class is not None:
        return frozenset({occupying_class.lesson_id})

    culprits: set[str] = set()
    eligible_rooms = problem.eligible_rooms_for(requirement, class_)
    for teacher in problem.eligible_teachers_for(requirement):
        if not problem.teacher_available(teacher.id, slot):
            continue  # static availability, not an earlier decision
        occupying_teacher = state.teacher_assignment_at(teacher.id, slot)
        if occupying_teacher is not None:
            culprits.add(occupying_teacher.lesson_id)
            continue
        # This teacher was free, so the rooms are what ruled the slot out.
        for room in eligible_rooms:
            occupying_room = state.room_assignment_at(room.id, slot)
            if occupying_room is not None:
                culprits.add(occupying_room.lesson_id)
    return frozenset(culprits)


def domain_wipeout_culprits(
    lesson: Lesson,
    domain: Sequence[TimeSlot],
    state: ScheduleState,
    problem: SchedulingProblem,
) -> frozenset[str]:
    """Why `lesson` has no placeable slot left: the union of what blocked
    it in each slot it still nominally had. Used when forward checking
    wipes a domain out — the lessons named here are exactly the ones whose
    reconsideration could give `lesson` a slot back."""
    culprits: set[str] = set()
    for slot in domain:
        culprits |= blocking_lesson_ids(lesson, slot, state, problem)
    return frozenset(culprits)
