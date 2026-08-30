"""Teacher entity (docs/04-DESIGN.md #1-2)."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Teacher:
    id: str
    school_id: str
    name: str
    email: str
    subject_ids: frozenset[str] = field(default_factory=frozenset)
    max_weekly_load: int = 30
    max_consecutive: int = 4

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Teacher.id must not be empty")
        if not self.school_id:
            raise ValueError("Teacher.school_id must not be empty")
        if not self.name:
            raise ValueError("Teacher.name must not be empty")
        if "@" not in self.email or self.email.startswith("@") or self.email.endswith("@"):
            raise ValueError(f"Teacher.email {self.email!r} is not a valid email address")
        if self.max_weekly_load <= 0:
            raise ValueError("Teacher.max_weekly_load must be > 0")
        if self.max_consecutive <= 0:
            raise ValueError("Teacher.max_consecutive must be > 0")

    def can_teach(self, subject_id: str) -> bool:
        return subject_id in self.subject_ids
