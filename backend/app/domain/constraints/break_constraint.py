"""HC-007: no lesson may be assigned to a period marked as a mandatory
break (docs/02-PRD.md #17). Breaks are periods, not a separate schedule
dimension (docs/04-DESIGN.md #2)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.violation import Severity, Violation
from app.domain.models.enums import TimePeriodKind
from app.domain.models.school import TimePeriod

if TYPE_CHECKING:
    from app.domain.scheduling.candidate import CandidateAssignment
    from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class BreakConstraint:
    id: ClassVar[str] = "HC-007"

    time_periods: Sequence[TimePeriod]
    _kind_by_period_id: dict[str, TimePeriodKind] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_kind_by_period_id",
            {period.id: period.kind for period in self.time_periods},
        )

    def _is_break(self, time_period_id: str) -> bool:
        return self._kind_by_period_id.get(time_period_id) is TimePeriodKind.BREAK

    def is_satisfied(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        return not self._is_break(candidate.time_slot.time_period_id)

    def explain_violation(self, state: ScheduleState, candidate: CandidateAssignment) -> Violation:
        return Violation(
            constraint_id=self.id,
            severity=Severity.ERROR,
            message=f"Period {candidate.time_slot.time_period_id} is a mandatory break",
            involved_entities=(candidate.time_slot.time_period_id, candidate.lesson_id),
        )

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        return [
            Violation(
                constraint_id=self.id,
                severity=Severity.ERROR,
                message=f"Period {a.time_slot.time_period_id} is a mandatory break",
                involved_entities=(a.time_slot.time_period_id, a.lesson_id),
            )
            for a in state.assignments
            if self._is_break(a.time_slot.time_period_id)
        ]
