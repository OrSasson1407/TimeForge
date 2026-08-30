from app.domain.constraints.preferences import (
    TeacherPreferredDayConstraint,
    TeacherPreferredPeriodConstraint,
)
from app.domain.models.availability import Availability
from app.domain.models.enums import OwnerType
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import ScheduleState

from .conftest import make_candidate

SLOT = TimeSlot(day_id="day_mon", time_period_id="p1")


def _availability(**overrides: object) -> Availability:
    defaults: dict[str, object] = {
        "id": "a1",
        "school_id": "s1",
        "owner_type": OwnerType.TEACHER,
        "owner_id": "t1",
        "time_period_id": "p1",
        "is_available": True,
    }
    defaults.update(overrides)
    return Availability(**defaults)  # type: ignore[arg-type]


def test_preferred_period_no_penalty_with_no_records() -> None:
    constraint = TeacherPreferredPeriodConstraint(weight=1.0, availability_records=[])
    state = ScheduleState(assignments=(make_candidate(teacher_id="t1", time_slot=SLOT),))

    assert constraint.penalty(state) == 0.0
    assert constraint.explain(state) == []


def test_preferred_period_penalizes_disliked_day_independent_period() -> None:
    record = _availability(day_id=None, preference_weight=-2.0)
    constraint = TeacherPreferredPeriodConstraint(weight=1.5, availability_records=[record])
    state = ScheduleState(assignments=(make_candidate(teacher_id="t1", time_slot=SLOT),))

    assert constraint.penalty(state) == 2.0
    contributions = constraint.explain(state)
    assert len(contributions) == 1
    assert contributions[0].constraint_id == "SC-001"
    assert contributions[0].raw_penalty == 2.0
    assert contributions[0].weighted_penalty == 3.0


def test_preferred_period_ignores_day_specific_records() -> None:
    record = _availability(day_id="day_mon", preference_weight=-2.0)
    constraint = TeacherPreferredPeriodConstraint(weight=1.0, availability_records=[record])
    state = ScheduleState(assignments=(make_candidate(teacher_id="t1", time_slot=SLOT),))

    assert constraint.penalty(state) == 0.0


def test_preferred_period_never_gives_a_bonus_for_liked_periods() -> None:
    record = _availability(day_id=None, preference_weight=5.0)
    constraint = TeacherPreferredPeriodConstraint(weight=1.0, availability_records=[record])
    state = ScheduleState(assignments=(make_candidate(teacher_id="t1", time_slot=SLOT),))

    assert constraint.penalty(state) == 0.0


def test_preferred_day_penalizes_disliked_day_specific_period() -> None:
    record = _availability(day_id="day_mon", preference_weight=-1.0)
    constraint = TeacherPreferredDayConstraint(weight=1.0, availability_records=[record])
    state = ScheduleState(assignments=(make_candidate(teacher_id="t1", time_slot=SLOT),))

    assert constraint.penalty(state) == 1.0
    assert constraint.explain(state)[0].constraint_id == "SC-002"


def test_preferred_day_ignores_day_independent_records() -> None:
    record = _availability(day_id=None, preference_weight=-1.0)
    constraint = TeacherPreferredDayConstraint(weight=1.0, availability_records=[record])
    state = ScheduleState(assignments=(make_candidate(teacher_id="t1", time_slot=SLOT),))

    assert constraint.penalty(state) == 0.0
