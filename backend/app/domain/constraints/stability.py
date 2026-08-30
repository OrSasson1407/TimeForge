"""SC-009, SC-010: minimize disruption during rescheduling, and preserve
previously published assignments when regenerating (docs/02-PRD.md #18).
Structurally identical — both penalize deviation from a baseline set of
assignments — but used in different contexts (SC-009: the pre-disruption
state, during rescheduling, Phase 9; SC-010: the prior published version,
during regeneration) and so kept as two distinctly-identified constraints
rather than one, matching docs/04-DESIGN.md #12's separate SC-ids.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.score import PenaltyContribution

if TYPE_CHECKING:
    from app.domain.scheduling.candidate import CandidateAssignment
    from app.domain.scheduling.state import ScheduleState


def _changed_lesson_ids(
    state: ScheduleState, baseline_by_lesson_id: dict[str, CandidateAssignment]
) -> list[str]:
    changed = []
    for assignment in state.assignments:
        baseline = baseline_by_lesson_id.get(assignment.lesson_id)
        if baseline is None:
            continue
        if (baseline.teacher_id, baseline.room_id, baseline.time_slot) != (
            assignment.teacher_id,
            assignment.room_id,
            assignment.time_slot,
        ):
            changed.append(assignment.lesson_id)
    return changed


@dataclass(frozen=True, slots=True)
class DisruptionMinimizationConstraint:
    id: ClassVar[str] = "SC-009"

    weight: float
    baseline: Sequence[CandidateAssignment]
    _baseline_by_lesson_id: dict[str, CandidateAssignment] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_baseline_by_lesson_id", {a.lesson_id: a for a in self.baseline})

    def penalty(self, state: ScheduleState) -> float:
        return float(len(_changed_lesson_ids(state, self._baseline_by_lesson_id)))

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        changed = _changed_lesson_ids(state, self._baseline_by_lesson_id)
        if not changed:
            return []
        return [
            PenaltyContribution(
                constraint_id=self.id,
                weight=self.weight,
                raw_penalty=float(len(changed)),
                weighted_penalty=self.weight * len(changed),
                message=f"{len(changed)} lesson(s) moved relative to the pre-disruption schedule",
            )
        ]


@dataclass(frozen=True, slots=True)
class PreservationConstraint:
    id: ClassVar[str] = "SC-010"

    weight: float
    baseline: Sequence[CandidateAssignment]
    _baseline_by_lesson_id: dict[str, CandidateAssignment] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_baseline_by_lesson_id", {a.lesson_id: a for a in self.baseline})

    def penalty(self, state: ScheduleState) -> float:
        return float(len(_changed_lesson_ids(state, self._baseline_by_lesson_id)))

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        changed = _changed_lesson_ids(state, self._baseline_by_lesson_id)
        if not changed:
            return []
        return [
            PenaltyContribution(
                constraint_id=self.id,
                weight=self.weight,
                raw_penalty=float(len(changed)),
                weighted_penalty=self.weight * len(changed),
                message=f"{len(changed)} lesson(s) changed relative to the prior published version",
            )
        ]
