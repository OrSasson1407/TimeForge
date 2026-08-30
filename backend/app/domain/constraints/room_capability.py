"""HC-004: a lesson requiring a room capability must be assigned a room
that has it (docs/02-PRD.md #17). The only mechanism linking subjects to
rooms — never a hardcoded subject-name check (master prompt #55)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.violation import Severity, Violation
from app.domain.models.lesson import Lesson, LessonRequirement
from app.domain.models.room import Room

if TYPE_CHECKING:
    from app.domain.scheduling.candidate import CandidateAssignment
    from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class RoomCapabilityConstraint:
    id: ClassVar[str] = "HC-004"

    lessons: Sequence[Lesson]
    requirements: Sequence[LessonRequirement]
    rooms: Sequence[Room]
    _required_capability_by_lesson_id: dict[str, str | None] = field(
        init=False, repr=False, compare=False
    )
    _capabilities_by_room_id: dict[str, frozenset[str]] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        requirement_by_id = {requirement.id: requirement for requirement in self.requirements}
        required_capability_by_lesson_id = {
            lesson.id: requirement_by_id[lesson.requirement_id].required_capability
            for lesson in self.lessons
            if lesson.requirement_id in requirement_by_id
        }
        object.__setattr__(
            self, "_required_capability_by_lesson_id", required_capability_by_lesson_id
        )
        object.__setattr__(
            self,
            "_capabilities_by_room_id",
            {room.id: room.capabilities for room in self.rooms},
        )

    def _violation_reason(self, candidate: CandidateAssignment) -> str | None:
        required = self._required_capability_by_lesson_id.get(candidate.lesson_id)
        if required is None:
            return None
        room_capabilities = self._capabilities_by_room_id.get(candidate.room_id, frozenset())
        if required in room_capabilities:
            return None
        return required

    def is_satisfied(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        return self._violation_reason(candidate) is None

    def explain_violation(self, state: ScheduleState, candidate: CandidateAssignment) -> Violation:
        required = self._violation_reason(candidate)
        assert required is not None
        return Violation(
            constraint_id=self.id,
            severity=Severity.ERROR,
            message=f"Room {candidate.room_id} lacks required capability {required} "
            f"for lesson {candidate.lesson_id}",
            involved_entities=(candidate.room_id, candidate.lesson_id, required),
        )

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        violations = []
        for a in state.assignments:
            required = self._violation_reason(a)
            if required is not None:
                violations.append(
                    Violation(
                        constraint_id=self.id,
                        severity=Severity.ERROR,
                        message=f"Room {a.room_id} lacks required capability {required} "
                        f"for lesson {a.lesson_id}",
                        involved_entities=(a.room_id, a.lesson_id, required),
                    )
                )
        return violations
