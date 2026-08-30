"""Schedule, ScheduleVersion, and ScheduleAssignment entities
(docs/04-DESIGN.md #1-2, #21; docs/05-DATABASE.md #16).
"""

from dataclasses import dataclass
from datetime import datetime

from app.domain.models.enums import ScheduleVersionStatus


@dataclass(frozen=True, slots=True)
class Schedule:
    """One per school; points at the currently active (published) version."""

    id: str
    school_id: str
    active_version_id: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Schedule.id must not be empty")
        if not self.school_id:
            raise ValueError("Schedule.school_id must not be empty")


@dataclass(frozen=True, slots=True)
class ScheduleScoreSummary:
    """The persisted score summary on a ScheduleVersion (docs/05-DATABASE.md #4).

    Distinct from the scheduling engine's internal Score value object
    (docs/04-DESIGN.md #3), which additionally carries a per-constraint
    breakdown used only during/just after a solve, not persisted long-term.
    """

    hard_violations: int
    soft_penalty: float
    quality: float

    def __post_init__(self) -> None:
        if self.hard_violations < 0:
            raise ValueError("ScheduleScoreSummary.hard_violations must be >= 0")
        if self.soft_penalty < 0:
            raise ValueError("ScheduleScoreSummary.soft_penalty must be >= 0")
        if not (0 < self.quality <= 100):
            raise ValueError("ScheduleScoreSummary.quality must be in (0, 100]")


@dataclass(frozen=True, slots=True)
class ScheduleVersion:
    """An immutable-once-published snapshot (docs/04-DESIGN.md #21).

    Field set includes `reason`, `assignment_count`, and `version_tag` in
    addition to the ones shown in docs/04-DESIGN.md #1's simplified class
    diagram — these are required by the concurrency model (docs/04-DESIGN.md
    #30) and the persisted document shape (docs/05-DATABASE.md #4).
    """

    id: str
    schedule_id: str
    status: ScheduleVersionStatus
    created_by: str
    created_at: datetime
    parent_version_id: str | None = None
    score: ScheduleScoreSummary | None = None
    reason: str | None = None
    assignment_count: int = 0
    version_tag: int = 0
    #: The client-supplied idempotency key that produced this version
    #: (docs/04-DESIGN.md #"Idempotency"), None for versions created
    #: through a path that doesn't require one (e.g. a manual move never
    #: creates a version, only `generate`/`reschedule` do).
    request_id: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("ScheduleVersion.id must not be empty")
        if not self.schedule_id:
            raise ValueError("ScheduleVersion.schedule_id must not be empty")
        if not self.created_by:
            raise ValueError("ScheduleVersion.created_by must not be empty")
        if self.assignment_count < 0:
            raise ValueError("ScheduleVersion.assignment_count must be >= 0")
        if self.version_tag < 0:
            raise ValueError("ScheduleVersion.version_tag must be >= 0")

    @property
    def is_publishable(self) -> bool:
        """BR-005: a schedule cannot be published while it has unresolved
        hard-constraint violations."""
        return self.status is ScheduleVersionStatus.DRAFT and (
            self.score is not None and self.score.hard_violations == 0
        )


@dataclass(frozen=True, slots=True)
class ScheduleAssignment:
    """The placement of one Lesson at one TimeSlot within one ScheduleVersion."""

    id: str
    version_id: str
    lesson_id: str
    teacher_id: str
    class_id: str
    room_id: str
    time_period_id: str
    day_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "id",
            "version_id",
            "lesson_id",
            "teacher_id",
            "class_id",
            "room_id",
            "time_period_id",
            "day_id",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"ScheduleAssignment.{field_name} must not be empty")
