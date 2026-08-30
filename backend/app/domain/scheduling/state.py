"""ScheduleState (docs/04-DESIGN.md #10, #27): the set of assignments made so
far during a search (or an externally-constructed schedule to validate),
plus fast-lookup indexes for O(1) conflict checks.

Implemented as an immutable value: `with_assignment()` returns a NEW
ScheduleState rather than mutating in place (matching the `with(candidate)
-> ScheduleState` signature in docs/04-DESIGN.md #27's class diagram and the
`newState := state.with(candidate)` step in the backtracking pseudocode,
#15). This makes backtracking trivial and safe: a rejected branch simply
discards its derived state without needing to undo anything on the
original. At this project's scale (hundreds of lessons) the O(n) copy per
step is negligible (docs/07-CODE_STANDARDS.md #34: don't optimize what the
benchmarks haven't shown to matter).
"""

from dataclasses import dataclass, field

from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.candidate import CandidateAssignment

_SlotIndex = dict[tuple[str, TimeSlot], CandidateAssignment]


@dataclass(frozen=True)
class ScheduleState:
    assignments: tuple[CandidateAssignment, ...] = field(default_factory=tuple)
    by_teacher_slot: _SlotIndex = field(init=False, repr=False, compare=False)
    by_class_slot: _SlotIndex = field(init=False, repr=False, compare=False)
    by_room_slot: _SlotIndex = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        by_teacher_slot: _SlotIndex = {}
        by_class_slot: _SlotIndex = {}
        by_room_slot: _SlotIndex = {}
        for assignment in self.assignments:
            by_teacher_slot[(assignment.teacher_id, assignment.time_slot)] = assignment
            by_class_slot[(assignment.class_id, assignment.time_slot)] = assignment
            by_room_slot[(assignment.room_id, assignment.time_slot)] = assignment
        object.__setattr__(self, "by_teacher_slot", by_teacher_slot)
        object.__setattr__(self, "by_class_slot", by_class_slot)
        object.__setattr__(self, "by_room_slot", by_room_slot)

    def with_assignment(self, candidate: CandidateAssignment) -> "ScheduleState":
        return ScheduleState(assignments=(*self.assignments, candidate))

    def teacher_assignment_at(self, teacher_id: str, slot: TimeSlot) -> CandidateAssignment | None:
        return self.by_teacher_slot.get((teacher_id, slot))

    def class_assignment_at(self, class_id: str, slot: TimeSlot) -> CandidateAssignment | None:
        return self.by_class_slot.get((class_id, slot))

    def room_assignment_at(self, room_id: str, slot: TimeSlot) -> CandidateAssignment | None:
        return self.by_room_slot.get((room_id, slot))


EMPTY_SCHEDULE_STATE = ScheduleState()
