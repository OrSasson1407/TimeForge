import pytest

from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.candidate import CandidateAssignment


def test_candidate_assignment_valid() -> None:
    candidate = CandidateAssignment(
        lesson_id="l1",
        class_id="c1",
        teacher_id="t1",
        room_id="r1",
        time_slot=TimeSlot(day_id="day_mon", time_period_id="p1"),
    )

    assert candidate.lesson_id == "l1"


@pytest.mark.parametrize("field_name", ["lesson_id", "class_id", "teacher_id", "room_id"])
def test_candidate_assignment_rejects_empty_fields(field_name: str) -> None:
    kwargs = {
        "lesson_id": "l1",
        "class_id": "c1",
        "teacher_id": "t1",
        "room_id": "r1",
        "time_slot": TimeSlot(day_id="day_mon", time_period_id="p1"),
    }
    kwargs[field_name] = ""

    with pytest.raises(ValueError, match=field_name):
        CandidateAssignment(**kwargs)  # type: ignore[arg-type]
