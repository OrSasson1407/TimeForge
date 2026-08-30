"""DisruptionCost (docs/04-DESIGN.md #17's cost formulation): how much a
repair changed relative to the pre-disruption schedule — the number
FR-021/SC-009 exist to keep small, and what the frontend/audit surface to
the administrator so "minimal disruption" is a measured claim, not an
assertion.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.scheduling.candidate import CandidateAssignment


@dataclass(frozen=True, slots=True)
class DisruptionCost:
    moved_assignments: int
    changed_rooms: int
    changed_teachers: int
    soft_constraint_penalty_delta: float

    def __post_init__(self) -> None:
        if self.moved_assignments < 0 or self.changed_rooms < 0 or self.changed_teachers < 0:
            raise ValueError("DisruptionCost counts must be >= 0")
        if self.soft_constraint_penalty_delta < 0:
            raise ValueError("DisruptionCost.soft_constraint_penalty_delta must be >= 0 (floored)")

    @property
    def total(self) -> float:
        """`otherConfiguredPenalties` from docs/04-DESIGN.md #17's formula
        is omitted: no `SchedulingConfig` field motivates a per-change fixed
        cost today, so it would be an invented number, not a measured one."""
        return (
            self.moved_assignments
            + self.changed_rooms
            + self.changed_teachers
            + self.soft_constraint_penalty_delta
        )


def compute_disruption_cost(
    baseline: Sequence[CandidateAssignment],
    repaired: Sequence[CandidateAssignment],
    *,
    baseline_soft_penalty: float,
    repaired_soft_penalty: float,
) -> DisruptionCost:
    baseline_by_lesson = {a.lesson_id: a for a in baseline}
    moved = 0
    changed_rooms = 0
    changed_teachers = 0
    for assignment in repaired:
        before = baseline_by_lesson.get(assignment.lesson_id)
        if before is None:
            continue  # a newly-placed lesson has no prior baseline to have "changed" from
        if before.time_slot != assignment.time_slot:
            moved += 1
        if before.room_id != assignment.room_id:
            changed_rooms += 1
        if before.teacher_id != assignment.teacher_id:
            changed_teachers += 1

    return DisruptionCost(
        moved_assignments=moved,
        changed_rooms=changed_rooms,
        changed_teachers=changed_teachers,
        soft_constraint_penalty_delta=max(0.0, repaired_soft_penalty - baseline_soft_penalty),
    )
