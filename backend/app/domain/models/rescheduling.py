"""ReschedulingEvent entity (docs/04-DESIGN.md #1-2, #17).

`affected_slots` corrects a mismatch found while implementing Phase 9: the
simplified class diagram (docs/04-DESIGN.md #1) and the algorithm walkthrough
(docs/04-DESIGN.md's Scenario 4, `ReschedulingEvent(..., effectiveFrom=slot)`)
both describe a recurring-week TIME SLOT ("Tuesday, period 3"), not a
calendar `date` — this system has no calendar-date concept anywhere else
(`SchoolDay` is a `Weekday`, not a specific date; `TimePeriod` has no date
either), so a bare `date` could never actually be resolved against the
schedule. Plural (`affected_slots`, not a single `affected_slot`) because a
real disruption is often multi-period ("out sick for the whole day"), not
strictly one — a reasonable, minor generalization of the doc's literal
singular wording, not a departure from its intent.
"""

from dataclasses import dataclass
from datetime import datetime

from app.domain.models.enums import ReschedulingEventType
from app.domain.models.value_objects import TimeSlot


@dataclass(frozen=True, slots=True)
class ReschedulingEvent:
    """A recorded disruption that triggers a rescheduling run."""

    id: str
    schedule_id: str
    type: ReschedulingEventType
    target_entity_id: str
    affected_slots: tuple[TimeSlot, ...]
    reason: str
    reported_at: datetime

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("ReschedulingEvent.id must not be empty")
        if not self.schedule_id:
            raise ValueError("ReschedulingEvent.schedule_id must not be empty")
        if not self.target_entity_id:
            raise ValueError("ReschedulingEvent.target_entity_id must not be empty")
        if not self.affected_slots:
            raise ValueError("ReschedulingEvent.affected_slots must not be empty")
        if not self.reason:
            raise ValueError("ReschedulingEvent.reason must not be empty")
