"""School configuration entities (docs/04-DESIGN.md #1-2): School, SchoolDay,
TimePeriod, Break. Days/periods/breaks are all school-configurable data, never
hardcoded (master prompt #14)."""

from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.models.enums import TimePeriodKind, Weekday


@dataclass(frozen=True, slots=True)
class School:
    id: str
    name: str
    timezone: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("School.id must not be empty")
        if not self.name:
            raise ValueError("School.name must not be empty")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"School.timezone {self.timezone!r} is not a known IANA timezone"
            ) from exc


@dataclass(frozen=True, slots=True)
class SchoolDay:
    id: str
    school_id: str
    weekday: Weekday
    is_active: bool

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("SchoolDay.id must not be empty")
        if not self.school_id:
            raise ValueError("SchoolDay.school_id must not be empty")


@dataclass(frozen=True, slots=True)
class TimePeriod:
    id: str
    school_id: str
    index: int
    start_time: time
    end_time: time
    kind: TimePeriodKind

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("TimePeriod.id must not be empty")
        if not self.school_id:
            raise ValueError("TimePeriod.school_id must not be empty")
        if self.index < 0:
            raise ValueError("TimePeriod.index must be >= 0")
        if self.end_time <= self.start_time:
            raise ValueError("TimePeriod.end_time must be after start_time")

    @property
    def is_break(self) -> bool:
        return self.kind is TimePeriodKind.BREAK


@dataclass(frozen=True, slots=True)
class Break:
    id: str
    school_id: str
    time_period_id: str
    label: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Break.id must not be empty")
        if not self.school_id:
            raise ValueError("Break.school_id must not be empty")
        if not self.time_period_id:
            raise ValueError("Break.time_period_id must not be empty")
        if not self.label:
            raise ValueError("Break.label must not be empty")
