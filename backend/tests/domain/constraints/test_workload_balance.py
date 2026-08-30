from app.domain.constraints.workload_balance import ClassWorkloadBalanceConstraint
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import ScheduleState

from .conftest import make_candidate

DAYS = ["day_mon", "day_tue", "day_wed"]


def test_no_penalty_for_evenly_spread_lessons() -> None:
    constraint = ClassWorkloadBalanceConstraint(weight=1.0, active_day_ids=DAYS)
    state = ScheduleState(
        assignments=tuple(
            make_candidate(lesson_id=f"l{i}", class_id="c1", time_slot=TimeSlot(day, "p0"))
            for i, day in enumerate(DAYS)
        )
    )

    assert constraint.penalty(state) == 0.0


def test_penalizes_uneven_daily_load() -> None:
    constraint = ClassWorkloadBalanceConstraint(weight=1.5, active_day_ids=DAYS)
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id="l1", class_id="c1", time_slot=TimeSlot("day_mon", "p0")),
            make_candidate(lesson_id="l2", class_id="c1", time_slot=TimeSlot("day_mon", "p1")),
            make_candidate(lesson_id="l3", class_id="c1", time_slot=TimeSlot("day_mon", "p2")),
            # day_tue and day_wed have 0 lessons each.
        )
    )

    assert constraint.penalty(state) == 3.0  # spread = 3 - 0
    contribution = constraint.explain(state)[0]
    assert contribution.constraint_id == "SC-006"
    assert contribution.weighted_penalty == 4.5


def test_empty_active_days_produces_no_penalty() -> None:
    constraint = ClassWorkloadBalanceConstraint(weight=1.0, active_day_ids=[])
    state = ScheduleState(
        assignments=(make_candidate(class_id="c1", time_slot=TimeSlot("day_mon", "p0")),)
    )

    assert constraint.penalty(state) == 0.0
