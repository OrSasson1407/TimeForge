"""SoftConstraint protocol (docs/04-DESIGN.md #10, #12): the strategy
interface every SC-xxx implementation satisfies. Unlike HardConstraint,
soft constraints operate on the WHOLE schedule state (no per-candidate
pruning role — they influence quality, never validity) and carry their own
configured `weight` (docs/05-DATABASE.md #19 `schedulingConfig`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol, runtime_checkable

from app.domain.constraints.score import PenaltyContribution

if TYPE_CHECKING:
    from app.domain.scheduling.state import ScheduleState


@runtime_checkable
class SoftConstraint(Protocol):
    """A soft constraint (SC-xxx). May be violated when necessary
    (docs/02-PRD.md #18) — it only ever affects `Score.soft_penalty`,
    never `Score.hard_violations`."""

    id: ClassVar[str]

    @property
    def weight(self) -> float:
        """Read-only by design: every concrete constraint is a frozen
        dataclass, so declaring this as a plain (writable) attribute here
        would make pyright reject them as non-conforming implementations."""
        ...

    def penalty(self, state: ScheduleState) -> float:
        """RAW (unweighted) penalty this constraint assigns to `state`.
        `ConstraintEvaluator.score()` applies `weight` when aggregating
        (docs/04-DESIGN.md #13: `softPenalty := Σ weight_i * penalty_i`)."""
        ...

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        """One or more contributions (e.g. one per teacher, per class)
        whose raw penalties sum to `penalty(state)` — explainability is not
        an afterthought (docs/03-ARCHITECTURE.md #20)."""
        ...
