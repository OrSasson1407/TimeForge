"""SC-001, SC-002: prefer a teacher's declared preferred periods/days
(docs/02-PRD.md #18). Both read `Availability.preference_weight`, but from
different slices of the same records — SC-001 uses day-INDEPENDENT records
(a general "I like/dislike this period-of-day" signal); SC-002 uses
day-SPECIFIC ones (the only records that actually vary by day, since a
single per-owner "I like Tuesdays" record isn't part of the Availability
shape — see docs/04-DESIGN.md #2, Availability). A negative weight is a
dislike and costs penalty; a positive or absent weight costs nothing —
SC-001/SC-002 discourage disliked slots, they don't reward liked ones
(penalties are never negative, docs/04-DESIGN.md #3).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.score import PenaltyContribution
from app.domain.models.availability import Availability, AvailabilityIndex, build_availability_index
from app.domain.models.enums import OwnerType

if TYPE_CHECKING:
    from app.domain.scheduling.state import ScheduleState


def _per_teacher_dislike_totals(state: ScheduleState, index: AvailabilityIndex) -> dict[str, float]:
    totals: dict[str, float] = {}
    for assignment in state.assignments:
        weight = index.preference_weight(
            assignment.teacher_id, assignment.time_slot.day_id, assignment.time_slot.time_period_id
        )
        if weight < 0:
            totals[assignment.teacher_id] = totals.get(assignment.teacher_id, 0.0) - weight
    return totals


@dataclass(frozen=True, slots=True)
class TeacherPreferredPeriodConstraint:
    id: ClassVar[str] = "SC-001"

    weight: float
    availability_records: Sequence[Availability]
    _index: AvailabilityIndex = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        day_independent = [r for r in self.availability_records if r.day_id is None]
        object.__setattr__(
            self, "_index", build_availability_index(day_independent, OwnerType.TEACHER)
        )

    def penalty(self, state: ScheduleState) -> float:
        return sum(_per_teacher_dislike_totals(state, self._index).values())

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        return [
            PenaltyContribution(
                constraint_id=self.id,
                weight=self.weight,
                raw_penalty=raw,
                weighted_penalty=self.weight * raw,
                message=f"Teacher {teacher_id} is scheduled in generally disliked periods "
                f"({raw:.1f} weighted units)",
            )
            for teacher_id, raw in _per_teacher_dislike_totals(state, self._index).items()
        ]


@dataclass(frozen=True, slots=True)
class TeacherPreferredDayConstraint:
    id: ClassVar[str] = "SC-002"

    weight: float
    availability_records: Sequence[Availability]
    _index: AvailabilityIndex = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        day_specific = [r for r in self.availability_records if r.day_id is not None]
        object.__setattr__(
            self, "_index", build_availability_index(day_specific, OwnerType.TEACHER)
        )

    def penalty(self, state: ScheduleState) -> float:
        return sum(_per_teacher_dislike_totals(state, self._index).values())

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        return [
            PenaltyContribution(
                constraint_id=self.id,
                weight=self.weight,
                raw_penalty=raw,
                weighted_penalty=self.weight * raw,
                message=f"Teacher {teacher_id} is scheduled on specifically disliked days "
                f"({raw:.1f} weighted units)",
            )
            for teacher_id, raw in _per_teacher_dislike_totals(state, self._index).items()
        ]
