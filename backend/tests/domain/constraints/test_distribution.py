from datetime import time

from app.domain.constraints.distribution import (
    MAX_CONSECUTIVE_SAME_SUBJECT,
    ConsecutiveLessonConstraint,
    SubjectDistributionConstraint,
)
from app.domain.models.enums import TimePeriodKind
from app.domain.models.lesson import Lesson, LessonRequirement
from app.domain.models.school import TimePeriod
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.state import ScheduleState

from .conftest import make_candidate

REQUIREMENT = LessonRequirement(
    id="req1", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=3
)
LESSONS = REQUIREMENT.expand()


def _periods(n: int = 5) -> list[TimePeriod]:
    return [
        TimePeriod(
            id=f"p{i}",
            school_id="s1",
            index=i,
            start_time=time(8 + i, 0),
            end_time=time(8 + i, 45),
            kind=TimePeriodKind.LESSON,
        )
        for i in range(n)
    ]


def test_subject_distribution_no_penalty_when_spread_across_days() -> None:
    constraint = SubjectDistributionConstraint(weight=1.0, lessons=LESSONS)
    state = ScheduleState(
        assignments=tuple(
            make_candidate(lesson_id=lesson.id, time_slot=TimeSlot(f"day_{i}", "p0"))
            for i, lesson in enumerate(LESSONS)
        )
    )

    assert constraint.penalty(state) == 0.0


def test_subject_distribution_penalizes_same_day_clustering() -> None:
    constraint = SubjectDistributionConstraint(weight=2.0, lessons=LESSONS)
    state = ScheduleState(
        assignments=(
            make_candidate(lesson_id=LESSONS[0].id, time_slot=TimeSlot("day_mon", "p0")),
            make_candidate(lesson_id=LESSONS[1].id, time_slot=TimeSlot("day_mon", "p1")),
            make_candidate(lesson_id=LESSONS[2].id, time_slot=TimeSlot("day_tue", "p0")),
        )
    )

    # 3 lessons across 2 distinct days -> 1 "extra" same-day occurrence.
    assert constraint.penalty(state) == 1.0
    contribution = constraint.explain(state)[0]
    assert contribution.constraint_id == "SC-004"
    assert contribution.weighted_penalty == 2.0


def test_consecutive_lesson_allows_up_to_the_threshold() -> None:
    lessons = [Lesson(id=f"l{i}", requirement_id="req1", sequence_index=i) for i in range(1, 4)]
    constraint = ConsecutiveLessonConstraint(
        weight=1.0, lessons=lessons, requirements=[REQUIREMENT], time_periods=_periods()
    )
    assignments = tuple(
        make_candidate(lesson_id=lesson.id, class_id="c1", time_slot=TimeSlot("day_mon", f"p{i}"))
        for i, lesson in enumerate(lessons[:MAX_CONSECUTIVE_SAME_SUBJECT])
    )
    state = ScheduleState(assignments=assignments)

    assert constraint.penalty(state) == 0.0


def test_consecutive_lesson_penalizes_runs_beyond_the_threshold() -> None:
    lessons = [Lesson(id=f"l{i}", requirement_id="req1", sequence_index=i) for i in range(1, 4)]
    constraint = ConsecutiveLessonConstraint(
        weight=1.0, lessons=lessons, requirements=[REQUIREMENT], time_periods=_periods()
    )
    state = ScheduleState(
        assignments=tuple(
            make_candidate(
                lesson_id=lessons[i].id, class_id="c1", time_slot=TimeSlot("day_mon", f"p{i}")
            )
            for i in range(3)
        )
    )

    assert constraint.penalty(state) == 1.0  # the 3rd consecutive period overruns
    contribution = constraint.explain(state)[0]
    assert contribution.constraint_id == "SC-005"
