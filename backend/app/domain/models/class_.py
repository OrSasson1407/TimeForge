"""Class (student group) entity (docs/04-DESIGN.md #1-2).

Named `class_` (module) / `Class` (type) to keep the exact domain term used
throughout docs/04-DESIGN.md and docs/05-DATABASE.md, despite `class` being
a Python keyword (docs/07-CODE_STANDARDS.md #4 mandates consistent
terminology across code and documentation).
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Class:
    id: str
    school_id: str
    name: str
    grade: int
    student_count: int
    home_room_id: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Class.id must not be empty")
        if not self.school_id:
            raise ValueError("Class.school_id must not be empty")
        if not self.name:
            raise ValueError("Class.name must not be empty")
        if self.grade < 0:
            raise ValueError("Class.grade must be >= 0")
        if self.student_count <= 0:
            raise ValueError("Class.student_count must be > 0")
