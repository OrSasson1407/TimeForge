"""LessonRequirement and Lesson entities (docs/04-DESIGN.md #1-2).

A LessonRequirement expresses "this Class needs N weekly periods of this
Subject." The scheduling engine expands it into N unplaced Lesson
instances, each of which becomes schedulable independently.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LessonRequirement:
    id: str
    school_id: str
    class_id: str
    subject_id: str
    weekly_periods: int
    required_capability: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("LessonRequirement.id must not be empty")
        if not self.school_id:
            raise ValueError("LessonRequirement.school_id must not be empty")
        if not self.class_id:
            raise ValueError("LessonRequirement.class_id must not be empty")
        if not self.subject_id:
            raise ValueError("LessonRequirement.subject_id must not be empty")
        if self.weekly_periods <= 0:
            raise ValueError("LessonRequirement.weekly_periods must be > 0")

    def expand(self) -> list["Lesson"]:
        """Build the N unplaced Lesson instances this requirement implies."""
        return [
            Lesson(id=f"{self.id}_{i}", requirement_id=self.id, sequence_index=i)
            for i in range(1, self.weekly_periods + 1)
        ]


@dataclass(frozen=True, slots=True)
class Lesson:
    id: str
    requirement_id: str
    sequence_index: int

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Lesson.id must not be empty")
        if not self.requirement_id:
            raise ValueError("Lesson.requirement_id must not be empty")
        if self.sequence_index < 1:
            raise ValueError("Lesson.sequence_index must be >= 1")
