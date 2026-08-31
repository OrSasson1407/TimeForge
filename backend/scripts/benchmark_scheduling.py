"""Runs the Small/Medium/Large benchmark scenarios (docs/03-ARCHITECTURE.md
#30) against the solver, plus one rescheduling repair, and prints measured
results — no fabricated numbers (master prompt §48).

Usage: uv run python -m scripts.benchmark_scheduling
"""

import time
from datetime import UTC, datetime

from app.domain.constraints import compute_quality
from app.domain.models import ReschedulingEventType
from app.domain.models.rescheduling import ReschedulingEvent
from app.domain.rescheduling import (
    ReschedulingEngine,
    ReschedulingStatus,
    augment_availability_for_event,
    augment_rooms_for_event,
)
from app.domain.scheduling import Solver, build_scheduling_problem
from scripts.scenario_factory import large_scenario, medium_scenario, small_scenario


def run() -> None:
    solver = Solver()
    scenarios = [small_scenario(), medium_scenario(), large_scenario(timeout_seconds=180.0)]

    print(
        f"{'Scenario':<10} {'Classes':>7} {'Lessons':>8} {'Status':>11} "
        f"{'Duration(s)':>12} {'Candidates':>11} {'Backtracks':>11} {'Backjumps':>10} "
        f"{'SoftPenalty':>12} {'Quality':>8}"
    )
    for scenario in scenarios:
        problem = scenario.problem
        result = solver.solve(problem)
        soft_penalty = f"{result.score.soft_penalty:.1f}" if result.score else "-"
        quality = "-"
        if result.score:
            quality_value = compute_quality(
                result.score.soft_penalty,
                problem.config.quality_decay_k,
                lesson_count=len(problem.lessons),
            )
            quality = f"{quality_value:.1f}"
        print(
            f"{scenario.name:<10} {len(problem.classes):>7} {len(problem.lessons):>8} "
            f"{result.status.value:>11} {result.stats.duration_seconds:>12.3f} "
            f"{result.stats.candidates_tried:>11} {result.stats.backtracks:>11} "
            f"{result.stats.backjumps:>10} "
            f"{soft_penalty:>12} {quality:>8}"
        )
        if result.score and result.score.breakdown:
            by_constraint: dict[str, float] = {}
            for contribution in result.score.breakdown:
                by_constraint[contribution.constraint_id] = (
                    by_constraint.get(contribution.constraint_id, 0.0)
                    + contribution.weighted_penalty
                )
            for constraint_id, total in sorted(by_constraint.items()):
                print(f"    {constraint_id}: {total:.1f} weighted penalty")
        if result.status.value == "INFEASIBLE" and result.infeasibility:
            for bottleneck in result.infeasibility.bottlenecks[:5]:
                print(
                    f"    bottleneck: subject={bottleneck.subject_id} "
                    f"capability={bottleneck.required_capability} "
                    f"required={bottleneck.required} available={bottleneck.available} "
                    f"shortage={bottleneck.shortage}"
                )
            if result.infeasibility.note:
                print(f"    note: {result.infeasibility.note}")

    _benchmark_reschedule()


def _benchmark_reschedule() -> None:
    """One rescheduling repair on the Small scenario: disrupt the busiest
    teacher at one of their slots (docs/04-DESIGN.md #17's "freeze
    unaffected, repair the rest") and measure the repair itself, separately
    from the initial generation above."""
    scenario = small_scenario()
    baseline_result = Solver().solve(scenario.problem)
    if baseline_result.status.value != "VALID":
        print(f"\nreschedule    skipped (baseline generation was {baseline_result.status.value})")
        return
    baseline = baseline_result.assignments

    counts: dict[str, int] = {}
    for assignment in baseline:
        counts[assignment.teacher_id] = counts.get(assignment.teacher_id, 0) + 1
    busiest_teacher_id = max(counts, key=lambda teacher_id: counts[teacher_id])
    disrupted = next(a for a in baseline if a.teacher_id == busiest_teacher_id)

    event = ReschedulingEvent(
        id="bench_ev1",
        schedule_id=scenario.school.id,
        type=ReschedulingEventType.TEACHER_UNAVAILABLE,
        target_entity_id=disrupted.teacher_id,
        affected_slots=(disrupted.time_slot,),
        reason="Benchmark disruption",
        reported_at=datetime.now(UTC),
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

    start = time.monotonic()
    outcome = ReschedulingEngine().reschedule(
        baseline, event, adjusted_problem, deadline=start + adjusted_problem.config.timeout_seconds
    )
    duration = time.monotonic() - start

    cost = outcome.disruption_cost
    cost_summary = (
        f"moved={cost.moved_assignments} rooms={cost.changed_rooms} "
        f"teachers={cost.changed_teachers} penalty_delta={cost.soft_constraint_penalty_delta:.1f}"
        if cost is not None
        else "-"
    )
    print(
        f"\n{'reschedule':<10} {'-':>7} {len(baseline):>8} "
        f"{outcome.status.value:>11} {duration * 1000:>10.2f}ms {'-':>11} {'-':>11} "
        f"{'-':>12} {'-':>8}"
    )
    print(f"    disruption cost: {cost_summary}")
    if outcome.status is ReschedulingStatus.UNREPAIRABLE and outcome.infeasibility:
        print(f"    note: {outcome.infeasibility.note}")


if __name__ == "__main__":
    run()
