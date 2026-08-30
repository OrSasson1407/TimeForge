"""SC-003: minimize gaps (idle LESSON periods) in a teacher's daily
schedule (docs/02-PRD.md #18). A gap is a LESSON-kind period strictly
between a teacher's first and last assignment of the day that has no
assignment — a BREAK period in that range is not a missed opportunity and
never counts.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.score import PenaltyContribution
from app.domain.models.enums import TimePeriodKind
from app.domain.models.school import TimePeriod

if TYPE_CHECKING:
    from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class TeacherGapConstraint:
    id: ClassVar[str] = "SC-003"

    weight: float
    time_periods: Sequence[TimePeriod]
    _period_by_index: dict[int, TimePeriod] = field(init=False, repr=False, compare=False)
    _index_by_period_id: dict[str, int] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_period_by_index", {p.index: p for p in self.time_periods})
        object.__setattr__(self, "_index_by_period_id", {p.id: p.index for p in self.time_periods})

    def _is_lesson_index(self, index: int) -> bool:
        period = self._period_by_index.get(index)
        return period is not None and period.kind is TimePeriodKind.LESSON

    def _gaps_by_teacher(self, state: ScheduleState) -> dict[str, int]:
        by_teacher_day: dict[tuple[str, str], list[int]] = {}
        for assignment in state.assignments:
            index = self._index_by_period_id.get(assignment.time_slot.time_period_id)
            if index is None:
                continue
            key = (assignment.teacher_id, assignment.time_slot.day_id)
            by_teacher_day.setdefault(key, []).append(index)

        gaps: dict[str, int] = {}
        for (teacher_id, _day_id), indices in by_teacher_day.items():
            if len(indices) < 2:
                continue
            indices.sort()
            occupied = set(indices)
            gap_count = sum(
                1
                for i in range(indices[0], indices[-1] + 1)
                if i not in occupied and self._is_lesson_index(i)
            )
            if gap_count:
                gaps[teacher_id] = gaps.get(teacher_id, 0) + gap_count
        return gaps

    def penalty(self, state: ScheduleState) -> float:
        return float(sum(self._gaps_by_teacher(state).values()))

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        return [
            PenaltyContribution(
                constraint_id=self.id,
                weight=self.weight,
                raw_penalty=float(gap_count),
                weighted_penalty=self.weight * gap_count,
                message=f"Teacher {teacher_id} has {gap_count} idle period(s) between lessons",
            )
            for teacher_id, gap_count in self._gaps_by_teacher(state).items()
        ]
