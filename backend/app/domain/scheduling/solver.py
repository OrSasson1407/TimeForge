"""Solver (docs/04-DESIGN.md #14-15): backtracking CSP search with forward
checking, dynamic MRV/degree lesson selection, and LCV candidate ordering.

The search is iterative (an explicit stack), not native Python recursion —
functionally identical to the recursive pseudocode in docs/04-DESIGN.md
#15, but immune to Python's default recursion-limit ceiling (~1000), which
a few hundred lessons deep in the "Large" benchmark scenario
(docs/03-ARCHITECTURE.md #30) could realistically approach or exceed.
Backtracking needs no explicit "undo": `ScheduleState`/lesson domains are
immutable, so a failed branch's derived state is simply discarded when its
stack frame is popped — the parent's own state/domains were never touched.

Each frame explores TIME SLOTS (see `heuristics.LessonDomain`); for each
slot tried, `SchedulingProblem.resolve_placement` lazily picks a specific
(teacher, room) pair, which is then re-validated once through the full
ConstraintEvaluator (defense-in-depth, cheap at O(constraints) per actual
placement attempt) before being committed.
"""

import time
from dataclasses import dataclass, field

from app.domain.constraints.evaluator import ConstraintEvaluator
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.conflicts import (
    blocking_lesson_ids,
    domain_wipeout_culprits,
    every_assigned_lesson_id,
)
from app.domain.scheduling.heuristics import (
    LessonDomain,
    build_lesson_domains,
    compute_degrees,
    forward_check_detailed,
    least_constraining_value_order,
    select_next_lesson,
)
from app.domain.scheduling.infeasibility import InfeasibilityAnalyzer, InfeasibilityResult
from app.domain.scheduling.optimizer import SimulatedAnnealingOptimizer
from app.domain.scheduling.problem import SchedulingProblem
from app.domain.scheduling.result import ScheduleResult, SearchStats, SolverStatus
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE, ScheduleState


@dataclass
class SearchRunStats:
    """Mutable by design (unlike everything else in the search): pure
    observational bookkeeping, never consulted for a search decision."""

    candidates_tried: int = 0
    backtracks: int = 0
    backjumps: int = 0


@dataclass
class _Frame:
    state: ScheduleState
    remaining: tuple[LessonDomain, ...]
    lesson_index: int | None = None
    candidates: list[TimeSlot] | None = None
    next_index: int = 0
    #: Lessons already placed *before* this frame that were implicated in
    #: one of this frame's failed placements — the conflict set driving
    #: backjumping (see `scheduling/conflicts.py`).
    conflict_set: set[str] = field(default_factory=set)

    @property
    def current_lesson_id(self) -> str | None:
        """The lesson this frame is currently trying to place, if it has
        picked one yet."""
        if self.lesson_index is None:
            return None
        return self.remaining[self.lesson_index][0].id


@dataclass(frozen=True, slots=True)
class SearchOutcome:
    kind: str  # "success" | "failure" | "timeout"
    state: ScheduleState


def run_search(
    initial_state: ScheduleState,
    initial_domains: tuple[LessonDomain, ...],
    degrees: dict[str, int],
    problem: SchedulingProblem,
    evaluator: ConstraintEvaluator,
    deadline: float,
    stats: SearchRunStats,
) -> SearchOutcome:
    """The backtracking search itself, parametrized by a starting state
    (docs/04-DESIGN.md #15, #17) — `Solver.solve()` calls this with
    `EMPTY_SCHEDULE_STATE` for a full generation; `ReschedulingEngine`
    (`app/domain/rescheduling/engine.py`) calls it with a state pre-loaded
    with the *frozen* (unaffected) assignments and domains built only for
    the lessons that need re-placing, so both are "the same solver"
    (docs/04-DESIGN.md #17's "same solver as §15") rather than two
    implementations of search.
    """
    # One full sweep up front, because `initial_domains` is built from the
    # problem alone (`candidate_slots_for`) and has never been reconciled
    # with `initial_state` — which matters for rescheduling, where that
    # state arrives pre-loaded with frozen assignments. Every later check is
    # incremental against the single slot just consumed, which is exactly
    # equivalent once this baseline is established (see
    # `forward_check_detailed`).
    initial_check = forward_check_detailed(initial_state, initial_domains, problem)
    if initial_check.pruned is None:
        return SearchOutcome(kind="failure", state=initial_state)

    stack: list[_Frame] = [_Frame(state=initial_state, remaining=initial_check.pruned)]
    deepest_state = initial_state

    while stack:
        if time.monotonic() > deadline:
            return SearchOutcome(kind="timeout", state=deepest_state)

        frame = stack[-1]

        if not frame.remaining:
            return SearchOutcome(kind="success", state=frame.state)

        if frame.lesson_index is None:
            frame.lesson_index = select_next_lesson(frame.remaining, degrees)
        lesson, domain = frame.remaining[frame.lesson_index]
        rest = frame.remaining[: frame.lesson_index] + frame.remaining[frame.lesson_index + 1 :]

        if frame.candidates is None:
            frame.candidates = list(least_constraining_value_order(domain, rest))

        advanced = False
        while frame.next_index < len(frame.candidates):
            slot = frame.candidates[frame.next_index]
            frame.next_index += 1
            stats.candidates_tried += 1

            candidate = problem.resolve_placement(lesson, slot, frame.state)
            if candidate is None:
                frame.conflict_set |= blocking_lesson_ids(lesson, slot, frame.state, problem)
                continue
            if not evaluator.is_candidate_valid(frame.state, candidate):
                # Rejected by a hard constraint beyond the teacher/class/room
                # clashes resolve_placement already screens for (capability,
                # capacity, a break period, ...). Those can depend on the
                # whole state in ways this layer can't attribute cheaply, so
                # take the always-safe superset rather than risk an
                # under-approximate conflict set (see conflicts.py).
                frame.conflict_set |= every_assigned_lesson_id(frame.state)
                continue

            new_state = frame.state.with_assignment(candidate)
            if len(new_state.assignments) > len(deepest_state.assignments):
                deepest_state = new_state
            check = forward_check_detailed(new_state, rest, problem, changed_slot=slot)
            if check.pruned is None:
                assert check.wiped_out is not None  # guaranteed when pruned is None
                # `lesson` itself is excluded: it is this frame's own
                # variable, and trying its other slots is precisely what
                # this loop is already doing.
                frame.conflict_set |= domain_wipeout_culprits(
                    check.wiped_out, check.wiped_domain, new_state, problem
                ) - {lesson.id}
                continue

            stack.append(_Frame(state=new_state, remaining=check.pruned, conflict_set=set()))
            advanced = True
            break

        if not advanced:
            stats.backtracks += 1
            failed = stack.pop()
            # Standard CBJ: jump to the deepest still-open decision that is
            # actually implicated, absorbing the failed frame's reasons on
            # the way. Every frame skipped is a subtree chronological
            # backtracking would have re-explored only to fail identically.
            conflict = set(failed.conflict_set)
            conflict.discard(lesson.id)
            while stack:
                target = stack[-1]
                target_lesson_id = target.current_lesson_id
                if target_lesson_id is not None and target_lesson_id in conflict:
                    conflict.discard(target_lesson_id)
                    target.conflict_set |= conflict
                    break
                conflict |= target.conflict_set
                if target_lesson_id is not None:
                    conflict.discard(target_lesson_id)
                stack.pop()
                stats.backjumps += 1

    return SearchOutcome(kind="failure", state=deepest_state)


@dataclass(frozen=True, slots=True)
class Solver:
    """Stateless: all per-run state lives in the search stack, never on
    `self`, so one Solver instance is safe to reuse across problems."""

    def solve(self, problem: SchedulingProblem) -> ScheduleResult:
        start = time.monotonic()
        deadline = start + problem.config.timeout_seconds

        try:
            analyzer = InfeasibilityAnalyzer(problem)
            pre_check = analyzer.analyze()
            if pre_check.is_infeasible:
                return ScheduleResult(
                    status=SolverStatus.INFEASIBLE,
                    infeasibility=pre_check,
                    stats=SearchStats(duration_seconds=time.monotonic() - start),
                )

            evaluator = ConstraintEvaluator(
                hard_constraints=problem.hard_constraints, soft_constraints=problem.soft_constraints
            )
            initial_domains = build_lesson_domains(problem.lessons, problem)
            degrees = compute_degrees(problem.lessons, problem)
            accumulator = SearchRunStats()
            outcome = run_search(
                EMPTY_SCHEDULE_STATE,
                initial_domains,
                degrees,
                problem,
                evaluator,
                deadline,
                accumulator,
            )

            duration = time.monotonic() - start
            stats = SearchStats(
                candidates_tried=accumulator.candidates_tried,
                backtracks=accumulator.backtracks,
                backjumps=accumulator.backjumps,
                duration_seconds=duration,
            )

            if outcome.kind == "success":
                # Optimize within whatever's left of the overall timeout
                # budget (docs/04-DESIGN.md #15) — never optimizes an
                # invalid state (master prompt Phase 5: "do not optimize
                # before hard constraints are reliable"). With no soft
                # constraints registered, soft_penalty is trivially always
                # 0 — annealing would just shuffle valid assignments
                # aimlessly, so it's skipped entirely rather than run for
                # no purpose.
                optimized = (
                    SimulatedAnnealingOptimizer().optimize(
                        outcome.state, problem, evaluator, deadline
                    )
                    if problem.soft_constraints
                    else outcome.state
                )
                return ScheduleResult(
                    status=SolverStatus.VALID,
                    assignments=optimized.assignments,
                    score=evaluator.score(optimized),
                    stats=stats,
                )
            if outcome.kind == "timeout":
                score = evaluator.score(outcome.state) if outcome.state.assignments else None
                return ScheduleResult(
                    status=SolverStatus.TIMEOUT,
                    assignments=outcome.state.assignments,
                    score=score,
                    stats=stats,
                )

            diagnosis = analyzer.analyze(outcome.state)
            if not diagnosis.is_infeasible:
                # Search exhausted every option without a bottleneck the
                # analyzer could name (e.g. an interaction between multiple
                # otherwise-fine requirements) — still a genuine failure to
                # find a solution, just without a specific culprit.
                diagnosis = InfeasibilityResult(
                    note="No valid combination was found for the remaining lessons, "
                    "though no single resource shortage explains it — this is likely "
                    "an interaction between multiple requirement groups."
                )
            return ScheduleResult(
                status=SolverStatus.INFEASIBLE,
                assignments=outcome.state.assignments,
                infeasibility=diagnosis,
                stats=stats,
            )
        except Exception as exc:  # noqa: BLE001 - the solver must never raise; see docstring
            return ScheduleResult(
                status=SolverStatus.FAILED,
                error=f"{type(exc).__name__}: {exc}",
                stats=SearchStats(duration_seconds=time.monotonic() - start),
            )
