"""End-to-end solver checks against the realistic benchmark scenarios
(scripts/scenario_factory.py, docs/03-ARCHITECTURE.md #30), enforcing the
invariants required of every generated schedule (docs/02-PRD.md #17): no
teacher/class/room overlap, no hard-constraint violation, every weekly
requirement satisfied — plus, since Phase 5, a well-formed quality score.
Marked slow — skipped from the default fast run.
"""

import pytest

from app.domain.constraints import compute_quality
from app.domain.scheduling.problem import SchedulingProblem
from app.domain.scheduling.result import ScheduleResult, SolverStatus
from app.domain.scheduling.solver import Solver
from scripts.scenario_factory import large_scenario, medium_scenario, small_scenario
from tests.support.invariants import assert_no_invariant_violations

pytestmark = pytest.mark.slow


def _assert_valid_and_invariant_clean(problem: SchedulingProblem, result: ScheduleResult) -> None:
    assert result.status is SolverStatus.VALID
    assert_no_invariant_violations(problem, result.assignments)

    assert result.score is not None
    assert result.score.hard_violations == 0
    assert result.score.soft_penalty >= 0
    quality = compute_quality(
        result.score.soft_penalty,
        problem.config.quality_decay_k,
        lesson_count=len(problem.lessons),
    )
    assert 0 < quality <= 100


def test_small_scenario_resolves_to_a_clean_valid_schedule() -> None:
    scenario = small_scenario(timeout_seconds=30.0)

    result = Solver().solve(scenario.problem)

    _assert_valid_and_invariant_clean(scenario.problem, result)


def test_medium_scenario_resolves_to_a_clean_valid_schedule() -> None:
    scenario = medium_scenario(timeout_seconds=60.0)

    result = Solver().solve(scenario.problem)

    _assert_valid_and_invariant_clean(scenario.problem, result)


def test_large_scenario_resolves_to_a_clean_valid_schedule() -> None:
    # docs/03-ARCHITECTURE.md #30 measured 115.6s for Large on the machine
    # benchmarked in Phase 4; a slower machine can need meaningfully more
    # wall-clock time for the same search (0 backtracks either way — this
    # is throughput, not a correctness/algorithmic difference), so this
    # opt-in slow test gives a generous budget rather than assume parity
    # with a benchmark run on different hardware.
    scenario = large_scenario(timeout_seconds=400.0)

    result = Solver().solve(scenario.problem)

    _assert_valid_and_invariant_clean(scenario.problem, result)
