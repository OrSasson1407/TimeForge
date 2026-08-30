"""Violation value object (docs/04-DESIGN.md #3): the result of a failed
constraint check, carrying enough structure to build an explanation
(docs/03-ARCHITECTURE.md #20) without the frontend inventing its own text.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    """Hard constraints always violate at ERROR severity. WARNING is
    reserved for soft-constraint threshold breaches (Phase 5)."""

    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True, slots=True)
class Violation:
    constraint_id: str
    severity: Severity
    message: str
    involved_entities: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.constraint_id:
            raise ValueError("Violation.constraint_id must not be empty")
        if not self.message:
            raise ValueError("Violation.message must not be empty")
