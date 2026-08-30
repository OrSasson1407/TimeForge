"""SC-006: balance each class's daily lesson load across the week
(docs/02-PRD.md #18) — penalized as the spread (max - min) between a
class's busiest and quietest active day. `active_day_ids` must include
every day the class *could* be scheduled on, not just days it happens to
have a lesson on this week, or an empty day would silently never count
against the spread.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.score import PenaltyContribution

if TYPE_CHECKING:
    from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class ClassWorkloadBalanceConstraint:
    id: ClassVar[str] = "SC-006"

    weight: float
    active_day_ids: Sequence[str]

    def _spread_by_class(self, state: ScheduleState) -> dict[str, int]:
        counts: dict[tuple[str, str], int] = {}
        classes_seen: set[str] = set()
        for assignment in state.assignments:
            key = (assignment.class_id, assignment.time_slot.day_id)
            counts[key] = counts.get(key, 0) + 1
            classes_seen.add(assignment.class_id)

        spreads: dict[str, int] = {}
        for class_id in classes_seen:
            daily_counts = [counts.get((class_id, day_id), 0) for day_id in self.active_day_ids]
            if not daily_counts:
                continue
            spread = max(daily_counts) - min(daily_counts)
            if spread > 0:
                spreads[class_id] = spread
        return spreads

    def penalty(self, state: ScheduleState) -> float:
        return float(sum(self._spread_by_class(state).values()))

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        return [
            PenaltyContribution(
                constraint_id=self.id,
                weight=self.weight,
                raw_penalty=float(spread),
                weighted_penalty=self.weight * spread,
                message=f"Class {class_id} has a {spread}-lesson gap between its busiest and "
                "quietest day",
            )
            for class_id, spread in self._spread_by_class(state).items()
        ]
