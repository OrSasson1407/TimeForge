"""SC-008: optimize shared/specialized resource usage — minimize idle
specialized-room time (docs/02-PRD.md #18). Simplification: penalizes idle
ratio for every room that has at least one capability, without separately
weighing whether unmet demand for that capability exists elsewhere in the
schedule (which would require comparing against total system-wide demand,
not just this room's own occupancy) — documented here as a deliberate
scope reduction, not an oversight.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.score import PenaltyContribution
from app.domain.models.room import Room
from app.domain.models.value_objects import TimeSlot

if TYPE_CHECKING:
    from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class ResourceUtilizationConstraint:
    id: ClassVar[str] = "SC-008"

    weight: float
    rooms: Sequence[Room]
    time_slots: Sequence[TimeSlot]

    def _idle_ratio_by_room(self, state: ScheduleState) -> dict[str, float]:
        total_slots = len(self.time_slots)
        if total_slots == 0:
            return {}
        used_counts: dict[str, int] = {}
        for assignment in state.assignments:
            used_counts[assignment.room_id] = used_counts.get(assignment.room_id, 0) + 1

        ratios: dict[str, float] = {}
        for room in self.rooms:
            if not room.capabilities:
                continue
            used = used_counts.get(room.id, 0)
            idle_ratio = (total_slots - used) / total_slots
            if idle_ratio > 0:
                ratios[room.id] = idle_ratio
        return ratios

    def penalty(self, state: ScheduleState) -> float:
        return sum(self._idle_ratio_by_room(state).values())

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        return [
            PenaltyContribution(
                constraint_id=self.id,
                weight=self.weight,
                raw_penalty=ratio,
                weighted_penalty=self.weight * ratio,
                message=f"Room {room_id} is idle {ratio:.0%} of the week despite having "
                "specialized capabilities",
            )
            for room_id, ratio in self._idle_ratio_by_room(state).items()
        ]
