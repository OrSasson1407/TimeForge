"""CandidateAssignment (docs/04-DESIGN.md #27): a proposed, not-yet-persisted
placement of one Lesson at one TimeSlot, considered during search or manual
move validation.

Includes `class_id` in addition to the fields shown in docs/04-DESIGN.md
#27's simplified class diagram (`lessonId; teacherId; roomId; timeSlot`) —
without it, neither the class-conflict/class-availability constraints nor
ScheduleState's by-class-slot index could work without threading an extra
lesson->class lookup through every consumer. docs/04-DESIGN.md #27 has been
updated to match.
"""

from dataclasses import dataclass

from app.domain.models.value_objects import TimeSlot


@dataclass(frozen=True, slots=True)
class CandidateAssignment:
    lesson_id: str
    class_id: str
    teacher_id: str
    room_id: str
    time_slot: TimeSlot

    def __post_init__(self) -> None:
        for field_name in ("lesson_id", "class_id", "teacher_id", "room_id"):
            if not getattr(self, field_name):
                raise ValueError(f"CandidateAssignment.{field_name} must not be empty")
