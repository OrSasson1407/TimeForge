"""End-to-end rescheduling check against a realistic benchmark scenario
(docs/03-ARCHITECTURE.md #30, scripts/scenario_factory.py), enforcing the
exact same invariants required of a full generation (docs/02-PRD.md §17,
§35 Success Metrics: "...measured by the invariant test suite run against
every generated/rescheduled result") — not just the small, hand-built
problems in test_engine.py. Marked slow — skipped from the default fast run.
"""

import time
from datetime import UTC, datetime

import pytest

from app.domain.models import ReschedulingEventType
from app.domain.models.rescheduling import ReschedulingEvent
from app.domain.rescheduling.engine import ReschedulingEngine, ReschedulingStatus
from app.domain.rescheduling.problem_adjustment import (
    augment_availability_for_event,
    augment_rooms_for_event,
)
from app.domain.scheduling import Solver, build_scheduling_problem
from app.domain.scheduling.result import SolverStatus
from scripts.scenario_factory import small_scenario
from tests.support.invariants import assert_no_invariant_violations

pytestmark = pytest.mark.slow


def test_small_scenario_repairs_cleanly_around_a_teacher_disruption() -> None:
    scenario = small_scenario(timeout_seconds=30.0)
    baseline_result = Solver().solve(scenario.problem)
    assert baseline_result.status is SolverStatus.VALID
    baseline = baseline_result.assignments

    # Disrupt a teacher who has more than one assignment, at just one of
    # their slots — the realistic "out for one period" case, not "out for
    # their only lesson."
    counts: dict[str, int] = {}
    for assignment in baseline:
        counts[assignment.teacher_id] = counts.get(assignment.teacher_id, 0) + 1
    busiest_teacher_id = max(counts, key=lambda teacher_id: counts[teacher_id])
    disrupted = next(a for a in baseline if a.teacher_id == busiest_teacher_id)

    event = ReschedulingEvent(
        id="ev1",
        schedule_id=scenario.school.id,
        type=ReschedulingEventType.TEACHER_UNAVAILABLE,
        target_entity_id=disrupted.teacher_id,
        affected_slots=(disrupted.time_slot,),
        reason="Sick leave",
        reported_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    adjusted_problem = build_scheduling_problem(
        scenario.school.id,
        teachers=scenario.problem.teachers,
        classes=scenario.problem.classes,
        rooms=augment_rooms_for_event(scenario.problem.rooms, event),
        requirements=scenario.problem.requirements,
        availability=augment_availability_for_event(
            scenario.problem.availability, event, school_id=scenario.school.id
        ),
        school_days=scenario.school_days,
        time_periods=scenario.time_periods,
        config=scenario.problem.config,
    )

    outcome = ReschedulingEngine().reschedule(
        baseline, event, adjusted_problem, deadline=time.monotonic() + 30.0
    )

    assert outcome.status is ReschedulingStatus.REPAIRED
    assert_no_invariant_violations(adjusted_problem, outcome.assignments)

    # The disrupted lesson didn't just get placed right back where the
    # disruption said the teacher is unavailable.
    repaired = next(a for a in outcome.assignments if a.lesson_id == disrupted.lesson_id)
    assert not (
        repaired.teacher_id == disrupted.teacher_id and repaired.time_slot == disrupted.time_slot
    )

    # Unaffected assignments (everything except the one disrupted lesson)
    # are untouched — the whole point of "freeze unaffected, repair the rest."
    baseline_by_lesson = {a.lesson_id: a for a in baseline if a.lesson_id != disrupted.lesson_id}
    repaired_by_lesson = {a.lesson_id: a for a in outcome.assignments}
    for lesson_id, before in baseline_by_lesson.items():
        assert repaired_by_lesson[lesson_id] == before
