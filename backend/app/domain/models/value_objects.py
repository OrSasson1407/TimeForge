"""Domain value objects (docs/04-DESIGN.md #3)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimeSlot:
    """The atomic scheduling coordinate: one day, one time period.

    Compared and hashed by value so it can key lookup dicts (e.g. a
    teacher's booked slots) without any identity/equality surprises.
    """

    day_id: str
    time_period_id: str

    def __post_init__(self) -> None:
        if not self.day_id:
            raise ValueError("TimeSlot.day_id must not be empty")
        if not self.time_period_id:
            raise ValueError("TimeSlot.time_period_id must not be empty")
