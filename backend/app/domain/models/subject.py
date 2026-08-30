"""Subject entity (docs/04-DESIGN.md #1-2)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Subject:
    id: str
    school_id: str
    name: str
    code: str
    required_capability: str | None = None
    max_daily_occurrences: int = 1
    min_spacing_days: int = 0

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Subject.id must not be empty")
        if not self.school_id:
            raise ValueError("Subject.school_id must not be empty")
        if not self.name:
            raise ValueError("Subject.name must not be empty")
        if not self.code:
            raise ValueError("Subject.code must not be empty")
        if self.max_daily_occurrences <= 0:
            raise ValueError("Subject.max_daily_occurrences must be > 0")
        if self.min_spacing_days < 0:
            raise ValueError("Subject.min_spacing_days must be >= 0")
