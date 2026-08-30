"""HC-005, HC-006: a teacher/class cannot be assigned outside its declared
availability (docs/02-PRD.md #17).

Decision: an owner with NO Availability record for a given (day, TimePeriod)
is treated as available (opt-out model) — submitting availability means
marking exceptions (e.g. "I'm unavailable Tuesday afternoons"), not
filling in every period of the week explicitly.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.violation import Severity, Violation
from app.domain.models.availability import Availability, AvailabilityIndex, build_availability_index
from app.domain.models.enums import OwnerType

if TYPE_CHECKING:
    from app.domain.scheduling.candidate import CandidateAssignment
    from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class TeacherAvailabilityConstraint:
    id: ClassVar[str] = "HC-005"

    availability_records: Sequence[Availability]
    _index: AvailabilityIndex = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "_index", build_availability_index(self.availability_records, OwnerType.TEACHER)
        )

    def _is_available(self, candidate: CandidateAssignment) -> bool:
        return self._index.is_available(
            candidate.teacher_id, candidate.time_slot.day_id, candidate.time_slot.time_period_id
        )

    def is_satisfied(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        return self._is_available(candidate)

    def explain_violation(self, state: ScheduleState, candidate: CandidateAssignment) -> Violation:
        return Violation(
            constraint_id=self.id,
            severity=Severity.ERROR,
            message=f"Teacher {candidate.teacher_id} is not available in this period",
            involved_entities=(candidate.teacher_id, candidate.time_slot.time_period_id),
        )

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        return [
            Violation(
                constraint_id=self.id,
                severity=Severity.ERROR,
                message=f"Teacher {a.teacher_id} is not available in this period",
                involved_entities=(a.teacher_id, a.time_slot.time_period_id, a.lesson_id),
            )
            for a in state.assignments
            if not self._is_available(a)
        ]


@dataclass(frozen=True, slots=True)
class ClassAvailabilityConstraint:
    id: ClassVar[str] = "HC-006"

    availability_records: Sequence[Availability]
    _index: AvailabilityIndex = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "_index", build_availability_index(self.availability_records, OwnerType.CLASS)
        )

    def _is_available(self, candidate: CandidateAssignment) -> bool:
        return self._index.is_available(
            candidate.class_id, candidate.time_slot.day_id, candidate.time_slot.time_period_id
        )

    def is_satisfied(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        return self._is_available(candidate)

    def explain_violation(self, state: ScheduleState, candidate: CandidateAssignment) -> Violation:
        return Violation(
            constraint_id=self.id,
            severity=Severity.ERROR,
            message=f"Class {candidate.class_id} is not available in this period",
            involved_entities=(candidate.class_id, candidate.time_slot.time_period_id),
        )

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        return [
            Violation(
                constraint_id=self.id,
                severity=Severity.ERROR,
                message=f"Class {a.class_id} is not available in this period",
                involved_entities=(a.class_id, a.time_slot.time_period_id, a.lesson_id),
            )
            for a in state.assignments
            if not self._is_available(a)
        ]
