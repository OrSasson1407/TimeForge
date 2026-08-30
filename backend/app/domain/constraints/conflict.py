"""HC-001, HC-002, HC-003: a teacher/class/room cannot be assigned to two
lessons in the same time period (docs/02-PRD.md #17).

`is_satisfied` uses ScheduleState's O(1) slot indexes, valid because a
correctly-driven search only ever adds candidates that already passed this
check, so the index is always collision-free by construction.
`violations_in` instead scans the raw assignment list, since it must also
catch conflicts in an externally/manually constructed ScheduleState where
that invariant may not hold (e.g. property tests, docs/02-PRD.md #17).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.violation import Severity, Violation
from app.domain.models.value_objects import TimeSlot

if TYPE_CHECKING:
    from app.domain.scheduling.candidate import CandidateAssignment
    from app.domain.scheduling.state import ScheduleState


def _duplicate_groups(
    assignments: Sequence[CandidateAssignment], key: Callable[[CandidateAssignment], str]
) -> list[list[CandidateAssignment]]:
    groups: dict[tuple[str, TimeSlot], list[CandidateAssignment]] = defaultdict(list)
    for assignment in assignments:
        groups[(key(assignment), assignment.time_slot)].append(assignment)
    return [group for group in groups.values() if len(group) > 1]


@dataclass(frozen=True, slots=True)
class TeacherConflictConstraint:
    id: ClassVar[str] = "HC-001"

    def is_satisfied(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        existing = state.teacher_assignment_at(candidate.teacher_id, candidate.time_slot)
        return existing is None or existing.lesson_id == candidate.lesson_id

    def explain_violation(self, state: ScheduleState, candidate: CandidateAssignment) -> Violation:
        existing = state.teacher_assignment_at(candidate.teacher_id, candidate.time_slot)
        assert existing is not None
        return Violation(
            constraint_id=self.id,
            severity=Severity.ERROR,
            message=f"Teacher {candidate.teacher_id} is already teaching lesson "
            f"{existing.lesson_id} in this period",
            involved_entities=(candidate.teacher_id, existing.lesson_id, candidate.lesson_id),
        )

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        return [
            Violation(
                constraint_id=self.id,
                severity=Severity.ERROR,
                message=f"Teacher {group[0].teacher_id} has {len(group)} lessons "
                "scheduled in the same period",
                involved_entities=tuple(a.lesson_id for a in group),
            )
            for group in _duplicate_groups(state.assignments, lambda a: a.teacher_id)
        ]


@dataclass(frozen=True, slots=True)
class ClassConflictConstraint:
    id: ClassVar[str] = "HC-002"

    def is_satisfied(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        existing = state.class_assignment_at(candidate.class_id, candidate.time_slot)
        return existing is None or existing.lesson_id == candidate.lesson_id

    def explain_violation(self, state: ScheduleState, candidate: CandidateAssignment) -> Violation:
        existing = state.class_assignment_at(candidate.class_id, candidate.time_slot)
        assert existing is not None
        return Violation(
            constraint_id=self.id,
            severity=Severity.ERROR,
            message=f"Class {candidate.class_id} already has lesson {existing.lesson_id} "
            "in this period",
            involved_entities=(candidate.class_id, existing.lesson_id, candidate.lesson_id),
        )

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        return [
            Violation(
                constraint_id=self.id,
                severity=Severity.ERROR,
                message=f"Class {group[0].class_id} has {len(group)} lessons "
                "scheduled in the same period",
                involved_entities=tuple(a.lesson_id for a in group),
            )
            for group in _duplicate_groups(state.assignments, lambda a: a.class_id)
        ]


@dataclass(frozen=True, slots=True)
class RoomConflictConstraint:
    id: ClassVar[str] = "HC-003"

    def is_satisfied(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        existing = state.room_assignment_at(candidate.room_id, candidate.time_slot)
        return existing is None or existing.lesson_id == candidate.lesson_id

    def explain_violation(self, state: ScheduleState, candidate: CandidateAssignment) -> Violation:
        existing = state.room_assignment_at(candidate.room_id, candidate.time_slot)
        assert existing is not None
        return Violation(
            constraint_id=self.id,
            severity=Severity.ERROR,
            message=f"Room {candidate.room_id} already hosts lesson {existing.lesson_id} "
            "in this period",
            involved_entities=(candidate.room_id, existing.lesson_id, candidate.lesson_id),
        )

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        return [
            Violation(
                constraint_id=self.id,
                severity=Severity.ERROR,
                message=f"Room {group[0].room_id} hosts {len(group)} lessons in the same period",
                involved_entities=tuple(a.lesson_id for a in group),
            )
            for group in _duplicate_groups(state.assignments, lambda a: a.room_id)
        ]
