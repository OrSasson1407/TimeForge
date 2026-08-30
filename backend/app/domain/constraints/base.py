"""HardConstraint protocol (docs/04-DESIGN.md #10-11): the strategy
interface every HC-xxx implementation satisfies. New constraints extend the
system by implementing this protocol and registering with a
ConstraintEvaluator — no change to the solver core (docs/04-DESIGN.md #33).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol, runtime_checkable

from app.domain.constraints.violation import Violation

if TYPE_CHECKING:
    from app.domain.scheduling.candidate import CandidateAssignment
    from app.domain.scheduling.state import ScheduleState


@runtime_checkable
class HardConstraint(Protocol):
    """A hard constraint (HC-xxx). Must never be silently bypassed
    (docs/01-CLAUDE.md rule 8)."""

    id: ClassVar[str]

    def is_satisfied(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        """Fast, incremental check used during search to prune invalid
        branches: does adding `candidate` to `state` keep this constraint
        satisfied? Must not have side effects and must not look at any
        assignment other than `candidate` and what's already in `state`."""
        ...

    def explain_violation(self, state: ScheduleState, candidate: CandidateAssignment) -> Violation:
        """Precondition: `is_satisfied(state, candidate)` is False. Building
        an explanation for a satisfied candidate is undefined behavior."""
        ...

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        """Full-state scan: every violation of this constraint present in
        `state`, independent of how it was built. Used for validating an
        externally-constructed schedule (e.g. property/invariant tests,
        docs/02-PRD.md #17) rather than for search-time pruning."""
        ...
