"""ReschedulingEventRepository (docs/05-DATABASE.md #3:
`schedules/{scheduleId}/reschedulingEvents/{eventId}`): append-only — a
recorded disruption is a historical fact, never edited or deleted
(mirrors `AuditRepository`).
"""

from typing import Protocol

from app.domain.models import ReschedulingEvent


class ReschedulingEventRepository(Protocol):
    def append(self, event: ReschedulingEvent) -> None: ...

    def list_for_schedule(self, schedule_id: str) -> list[ReschedulingEvent]:
        """Newest first."""
        ...
