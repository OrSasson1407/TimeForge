"""HC-009: a room's assigned class size must not exceed the room's
capacity (docs/02-PRD.md #17)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.violation import Severity, Violation
from app.domain.models.class_ import Class
from app.domain.models.room import Room

if TYPE_CHECKING:
    from app.domain.scheduling.candidate import CandidateAssignment
    from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class RoomCapacityConstraint:
    id: ClassVar[str] = "HC-009"

    classes: Sequence[Class]
    rooms: Sequence[Room]
    _student_count_by_class_id: dict[str, int] = field(init=False, repr=False, compare=False)
    _capacity_by_room_id: dict[str, int] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_student_count_by_class_id",
            {class_.id: class_.student_count for class_ in self.classes},
        )
        object.__setattr__(
            self, "_capacity_by_room_id", {room.id: room.capacity for room in self.rooms}
        )

    def _overflow(self, candidate: CandidateAssignment) -> tuple[int, int] | None:
        student_count = self._student_count_by_class_id.get(candidate.class_id)
        capacity = self._capacity_by_room_id.get(candidate.room_id)
        if student_count is None or capacity is None or student_count <= capacity:
            return None
        return student_count, capacity

    def is_satisfied(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        return self._overflow(candidate) is None

    def explain_violation(self, state: ScheduleState, candidate: CandidateAssignment) -> Violation:
        overflow = self._overflow(candidate)
        assert overflow is not None
        student_count, capacity = overflow
        return Violation(
            constraint_id=self.id,
            severity=Severity.ERROR,
            message=f"Class {candidate.class_id} ({student_count} students) exceeds room "
            f"{candidate.room_id} capacity ({capacity})",
            involved_entities=(candidate.class_id, candidate.room_id),
        )

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        violations = []
        for a in state.assignments:
            overflow = self._overflow(a)
            if overflow is not None:
                student_count, capacity = overflow
                violations.append(
                    Violation(
                        constraint_id=self.id,
                        severity=Severity.ERROR,
                        message=f"Class {a.class_id} ({student_count} students) exceeds room "
                        f"{a.room_id} capacity ({capacity})",
                        involved_entities=(a.class_id, a.room_id, a.lesson_id),
                    )
                )
        return violations
