"""Adjusts raw catalog data to reflect a `ReschedulingEvent` BEFORE
`build_scheduling_problem` constructs the `SchedulingProblem` a repair runs
against (docs/04-DESIGN.md #17).

Without this, the repair search has no way to know the disrupted
teacher/room is unavailable — `SchedulingProblem`'s own availability index
and the `TeacherAvailabilityConstraint`/`RoomCapabilityConstraint`/etc. hard
constraints are each built once, independently, from the raw
availability/room lists at construction time (`build_scheduling_problem`),
so patching an already-built `SchedulingProblem` in place (e.g. via
`dataclasses.replace(problem, availability=...)`) would update the
problem's own index but leave every hard-constraint instance holding a
stale reference — a real, easy-to-miss bug class this module exists to
avoid entirely by adjusting the RAW inputs instead, before construction.
`ReschedulingEngine.reschedule()` therefore expects an already-adjusted
`SchedulingProblem`; building one is the caller's responsibility (typically
`RescheduleUseCase`, which has the raw catalog data to adjust).
"""

import dataclasses
from collections.abc import Sequence

from app.domain.models.availability import Availability
from app.domain.models.enums import OwnerType, ReschedulingEventType, RoomStatus
from app.domain.models.rescheduling import ReschedulingEvent
from app.domain.models.room import Room


def augment_availability_for_event(
    availability: Sequence[Availability], event: ReschedulingEvent, *, school_id: str
) -> tuple[Availability, ...]:
    """For `TEACHER_UNAVAILABLE`: adds a synthetic day-specific unavailable
    record per affected slot, which takes priority over any existing
    day-independent record for the same (teacher, period) — consistent
    with `Availability`'s own documented day-specific-overrides-day-
    independent rule. A no-op for every other event type."""
    if event.type is not ReschedulingEventType.TEACHER_UNAVAILABLE:
        return tuple(availability)
    synthetic = tuple(
        Availability(
            id=f"resched_block_{event.id}_{i}",
            school_id=school_id,
            owner_type=OwnerType.TEACHER,
            owner_id=event.target_entity_id,
            day_id=slot.day_id,
            time_period_id=slot.time_period_id,
            is_available=False,
        )
        for i, slot in enumerate(event.affected_slots)
    )
    return (*availability, *synthetic)


def augment_rooms_for_event(rooms: Sequence[Room], event: ReschedulingEvent) -> tuple[Room, ...]:
    """For `ROOM_UNAVAILABLE`: marks the target room `CLOSED` for the
    entire repair run. This domain model has no per-slot room availability
    (only the global `RoomStatus`), so "unavailable at these slots" is
    conservatively treated as "excluded from this repair's room choices
    entirely" — always correct (never proposes an actually-unavailable
    room), even where it's more conservative than a hypothetical per-slot
    model would need to be. A no-op for every other event type."""
    if event.type is not ReschedulingEventType.ROOM_UNAVAILABLE:
        return tuple(rooms)
    return tuple(
        dataclasses.replace(room, status=RoomStatus.CLOSED)
        if room.id == event.target_entity_id
        else room
        for room in rooms
    )
