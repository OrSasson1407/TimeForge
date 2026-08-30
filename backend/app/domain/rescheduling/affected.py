"""identify_affected_assignments (docs/04-DESIGN.md #17): the first step of
`ReschedulingEngine.reschedule` — selects exactly the assignments a
disruption event directly invalidates, so everything else can be frozen.
Only `TEACHER_UNAVAILABLE`/`ROOM_UNAVAILABLE` are implemented (see
docs/04-DESIGN.md #17's "Implemented event types" note).
"""

from collections.abc import Sequence

from app.domain.models.enums import ReschedulingEventType
from app.domain.models.rescheduling import ReschedulingEvent
from app.domain.scheduling.candidate import CandidateAssignment


class UnsupportedReschedulingEventTypeError(Exception):
    """Raised for a `ReschedulingEventType` the engine doesn't yet
    implement — never silently mishandled (master prompt: no fake
    features)."""


def identify_affected_assignments(
    assignments: Sequence[CandidateAssignment], event: ReschedulingEvent
) -> tuple[CandidateAssignment, ...]:
    affected_slots = set(event.affected_slots)

    if event.type is ReschedulingEventType.TEACHER_UNAVAILABLE:
        return tuple(
            a
            for a in assignments
            if a.teacher_id == event.target_entity_id and a.time_slot in affected_slots
        )
    if event.type is ReschedulingEventType.ROOM_UNAVAILABLE:
        return tuple(
            a
            for a in assignments
            if a.room_id == event.target_entity_id and a.time_slot in affected_slots
        )
    raise UnsupportedReschedulingEventTypeError(
        f"ReschedulingEngine does not yet support event type {event.type}"
    )
