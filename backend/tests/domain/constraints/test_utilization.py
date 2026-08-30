from app.domain.constraints.utilization import ResourceUtilizationConstraint
from app.domain.models.room import Room
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import ScheduleState

from .conftest import make_candidate

TIME_SLOTS = [TimeSlot(f"day_{i}", "p1") for i in range(4)]


def _lab_room() -> Room:
    return Room(
        id="r_lab",
        school_id="s1",
        name="Lab",
        capacity=30,
        room_type="LABORATORY",
        capabilities=frozenset({"CHEMISTRY_LAB"}),
    )


def test_fully_used_specialized_room_has_no_penalty() -> None:
    constraint = ResourceUtilizationConstraint(
        weight=1.0, rooms=[_lab_room()], time_slots=TIME_SLOTS
    )
    state = ScheduleState(
        assignments=tuple(
            make_candidate(lesson_id=f"l{i}", room_id="r_lab", time_slot=slot)
            for i, slot in enumerate(TIME_SLOTS)
        )
    )

    assert constraint.penalty(state) == 0.0


def test_idle_specialized_room_is_penalized() -> None:
    constraint = ResourceUtilizationConstraint(
        weight=2.0, rooms=[_lab_room()], time_slots=TIME_SLOTS
    )
    state = ScheduleState(
        assignments=(make_candidate(lesson_id="l1", room_id="r_lab", time_slot=TIME_SLOTS[0]),)
    )

    assert constraint.penalty(state) == 0.75  # 3 of 4 slots idle
    contribution = constraint.explain(state)[0]
    assert contribution.constraint_id == "SC-008"
    assert contribution.weighted_penalty == 1.5


def test_standard_room_without_capabilities_is_never_penalized() -> None:
    standard_room = Room(id="r_std", school_id="s1", name="Room", capacity=30, room_type="STANDARD")
    constraint = ResourceUtilizationConstraint(
        weight=1.0, rooms=[standard_room], time_slots=TIME_SLOTS
    )
    state = ScheduleState(assignments=())

    assert constraint.penalty(state) == 0.0
