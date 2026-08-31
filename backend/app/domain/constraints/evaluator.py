"""ConstraintEvaluator (docs/04-DESIGN.md #11, #14, #18): the single
choke point that aggregates all registered Hard- and SoftConstraint
instances. Reused, unmodified, by the solver's search loop, the annealing
optimizer, the rescheduling repair pass, and manual-move validation
(docs/01-CLAUDE.md rule 8, Architecture Principle 2) — there is exactly
one implementation of conflict detection and exactly one of scoring.

Hard constraints are checked in registration order; register the cheapest,
highest-selectivity checks first (conflict/index-lookup constraints before
constraints requiring an availability/capability lookup) so
`is_candidate_valid` short-circuits as early as possible
(docs/04-DESIGN.md #11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.domain.constraints.base import HardConstraint
from app.domain.constraints.score import PenaltyContribution, Score
from app.domain.constraints.soft_base import SoftConstraint
from app.domain.constraints.violation import Violation

if TYPE_CHECKING:
    from app.domain.scheduling.candidate import CandidateAssignment
    from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class ConstraintEvaluator:
    hard_constraints: tuple[HardConstraint, ...] = field(default_factory=tuple)
    soft_constraints: tuple[SoftConstraint, ...] = field(default_factory=tuple)

    def is_candidate_valid(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        return all(
            constraint.is_satisfied(state, candidate) for constraint in self.hard_constraints
        )

    def first_violation(
        self, state: ScheduleState, candidate: CandidateAssignment
    ) -> Violation | None:
        for constraint in self.hard_constraints:
            if not constraint.is_satisfied(state, candidate):
                return constraint.explain_violation(state, candidate)
        return None

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        violations: list[Violation] = []
        for constraint in self.hard_constraints:
            violations.extend(constraint.violations_in(state))
        return violations

    def soft_penalty(self, state: ScheduleState) -> float:
        """Just the weighted soft-constraint total, skipping the
        hard-violation scan that `score()` also performs.

        This exists for the annealing optimizer, which evaluates a candidate
        thousands of times and reads only this number. Calling `score()`
        there ran `violations_in` — a full O(assignments) sweep across every
        hard constraint — a second time per iteration and then discarded the
        result, which a profile showed to be the single largest cost in a
        solve. Computed from the same `explain()` breakdown `score()` sums,
        so the two can never disagree about the total.
        """
        return sum(
            contribution.weighted_penalty
            for constraint in self.soft_constraints
            for contribution in constraint.explain(state)
        )

    def score(self, state: ScheduleState) -> Score:
        """docs/04-DESIGN.md #13: hardViolations from a full violation
        scan (reusing `violations_in`, never a second implementation of
        conflict detection); softPenalty from each constraint's own
        `explain()` breakdown, so the returned breakdown and the total are
        always consistent by construction."""
        breakdown: list[PenaltyContribution] = []
        for constraint in self.soft_constraints:
            breakdown.extend(constraint.explain(state))
        soft_penalty = sum(contribution.weighted_penalty for contribution in breakdown)
        return Score(
            hard_violations=len(self.violations_in(state)),
            soft_penalty=soft_penalty,
            breakdown=tuple(breakdown),
        )
