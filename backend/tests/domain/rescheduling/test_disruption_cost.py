from app.domain.models.value_objects import TimeSlot
from app.domain.rescheduling.disruption_cost import compute_disruption_cost
from app.domain.scheduling.candidate import CandidateAssignment

SLOT_A = TimeSlot(day_id="mon", time_period_id="p1")
SLOT_B = TimeSlot(day_id="mon", time_period_id="p2")


def test_counts_moved_room_and_teacher_changes_independently() -> None:
    baseline = [
        CandidateAssignment(
            lesson_id="l1", class_id="c1", teacher_id="t1", room_id="r1", time_slot=SLOT_A
        ),
        CandidateAssignment(
            lesson_id="l2", class_id="c1", teacher_id="t1", room_id="r1", time_slot=SLOT_B
        ),
    ]
    repaired = [
        # everything about l1 changed: slot, room, and teacher.
        CandidateAssignment(
            lesson_id="l1", class_id="c1", teacher_id="t2", room_id="r2", time_slot=SLOT_B
        ),
        # l2 is untouched.
        CandidateAssignment(
            lesson_id="l2", class_id="c1", teacher_id="t1", room_id="r1", time_slot=SLOT_B
        ),
    ]

    cost = compute_disruption_cost(
        baseline, repaired, baseline_soft_penalty=10.0, repaired_soft_penalty=12.0
    )

    assert cost.moved_assignments == 1
    assert cost.changed_rooms == 1
    assert cost.changed_teachers == 1
    assert cost.soft_constraint_penalty_delta == 2.0
    assert cost.total == 5.0


def test_penalty_delta_is_floored_at_zero() -> None:
    cost = compute_disruption_cost([], [], baseline_soft_penalty=10.0, repaired_soft_penalty=4.0)

    assert cost.soft_constraint_penalty_delta == 0.0


def test_newly_placed_lesson_is_not_counted_as_a_change() -> None:
    repaired = [
        CandidateAssignment(
            lesson_id="new", class_id="c1", teacher_id="t1", room_id="r1", time_slot=SLOT_A
        )
    ]

    cost = compute_disruption_cost(
        [], repaired, baseline_soft_penalty=0.0, repaired_soft_penalty=0.0
    )

    assert cost.moved_assignments == 0
    assert cost.changed_rooms == 0
    assert cost.changed_teachers == 0


def test_unchanged_schedule_has_zero_cost() -> None:
    assignments = [
        CandidateAssignment(
            lesson_id="l1", class_id="c1", teacher_id="t1", room_id="r1", time_slot=SLOT_A
        )
    ]

    cost = compute_disruption_cost(
        assignments, assignments, baseline_soft_penalty=5.0, repaired_soft_penalty=5.0
    )

    assert cost.total == 0.0
