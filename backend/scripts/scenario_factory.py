"""Synthetic benchmark/demo scenarios (docs/03-ARCHITECTURE.md #30
Performance; master prompt §48). Deterministic given a seed (NFR-007) —
used by both `scripts/benchmark_scheduling.py` and the solver's
integration tests, so the two never drift apart.

Not "unrealistic random data that produces trivial schedules" (master
prompt §42): the subject/teacher/room ratios are sized so that hard
constraints are genuinely contended, not vacuously satisfied.
"""

import math
import random
from dataclasses import dataclass
from datetime import time

from app.domain.models import (
    Availability,
    Class,
    LessonRequirement,
    OwnerType,
    Room,
    School,
    SchoolDay,
    Teacher,
    TimePeriod,
    TimePeriodKind,
    Weekday,
)
from app.domain.scheduling import SchedulingConfig, SchedulingProblem, build_scheduling_problem

# (code, name, weekly_periods, required_capability)
SUBJECT_CATALOG = [
    ("MATH", "Mathematics", 5, None),
    ("LANG", "Language Arts", 4, None),
    ("SCI", "Science", 3, None),
    ("CHEM", "Chemistry", 2, "CHEMISTRY_LAB"),
    ("PE", "Physical Education", 2, "GYM"),
    ("ART", "Art", 1, None),
    ("MUSIC", "Music", 1, None),
    ("CS", "Computer Science", 2, "COMPUTER_LAB"),
    ("HIST", "History", 2, None),
    ("CIVICS", "Civics", 1, None),
]

ACTIVE_DAYS = [Weekday.SUNDAY, Weekday.MONDAY, Weekday.TUESDAY, Weekday.WEDNESDAY, Weekday.THURSDAY]

# (start, end, kind) for one day; 8 LESSON periods + 2 BREAKs.
DAY_TEMPLATE = [
    (time(8, 0), time(8, 45), TimePeriodKind.LESSON),
    (time(8, 45), time(9, 30), TimePeriodKind.LESSON),
    (time(9, 30), time(9, 45), TimePeriodKind.BREAK),
    (time(9, 45), time(10, 30), TimePeriodKind.LESSON),
    (time(10, 30), time(11, 15), TimePeriodKind.LESSON),
    (time(11, 15), time(12, 0), TimePeriodKind.LESSON),
    (time(12, 0), time(12, 30), TimePeriodKind.BREAK),
    (time(12, 30), time(13, 15), TimePeriodKind.LESSON),
    (time(13, 15), time(14, 0), TimePeriodKind.LESSON),
    (time(14, 0), time(14, 45), TimePeriodKind.LESSON),
]

LESSON_SLOTS_PER_WEEK = len(ACTIVE_DAYS) * sum(
    1 for _, _, kind in DAY_TEMPLATE if kind is TimePeriodKind.LESSON
)
ROOM_UTILIZATION_TARGET = 0.5

UNAVAILABILITY_RATE = 0.05


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    school: School
    problem: SchedulingProblem
    #: The raw calendar structure `problem` was built from — not
    #: reconstructible from `problem` alone (`SchedulingProblem` only
    #: stores the derived `time_slots`, not the `SchoolDay`/`TimePeriod`
    #: records themselves) — exposed for callers that need to rebuild an
    #: adjusted problem from the same raw inputs (e.g. the rescheduling
    #: engine's integration tests, which augment availability/rooms with a
    #: disruption before re-running `build_scheduling_problem`).
    school_days: tuple[SchoolDay, ...]
    time_periods: tuple[TimePeriod, ...]


def _build_days_and_periods(school_id: str) -> tuple[list[SchoolDay], list[TimePeriod]]:
    days = [
        SchoolDay(
            id=f"day_{weekday.value.lower()}", school_id=school_id, weekday=weekday, is_active=True
        )
        for weekday in ACTIVE_DAYS
    ]
    periods = [
        TimePeriod(
            id=f"period_{index}",
            school_id=school_id,
            index=index,
            start_time=start,
            end_time=end,
            kind=kind,
        )
        for index, (start, end, kind) in enumerate(DAY_TEMPLATE)
    ]
    return days, periods


def _build_classes(
    school_id: str, num_classes: int, home_room_ids: list[str], rng: random.Random
) -> list[Class]:
    classes = []
    for i in range(num_classes):
        grade = 7 + (i % 6)  # grades 7-12
        section = chr(ord("A") + (i // 6))
        classes.append(
            Class(
                id=f"class_{i}",
                school_id=school_id,
                name=f"{grade}{section}",
                grade=grade,
                student_count=rng.randint(20, 30),
                home_room_id=home_room_ids[i % len(home_room_ids)] if home_room_ids else None,
            )
        )
    return classes


def _build_teachers(school_id: str, num_classes: int, rng: random.Random) -> list[Teacher]:
    teachers_per_subject = max(2, round(num_classes / 5))
    teachers = []
    for subject_code, _, _, _ in SUBJECT_CATALOG:
        for i in range(teachers_per_subject):
            teacher_id = f"teacher_{subject_code}_{i}"
            teachers.append(
                Teacher(
                    id=teacher_id,
                    school_id=school_id,
                    name=f"{subject_code} Teacher {i}",
                    email=f"{teacher_id}@example.com",
                    subject_ids=frozenset({subject_code}),
                    max_weekly_load=28,
                    max_consecutive=4,
                )
            )
    return teachers


def _rooms_needed_for(num_classes: int, weekly_periods: int) -> int:
    """Enough rooms that a capability's total weekly demand uses at most
    ROOM_UTILIZATION_TARGET of the capacity a room offers — sizing a
    specialized room count directly off (classes x periods) rather than an
    arbitrary ratio avoids the near-zero-slack packing problems (very slow,
    heavily-backtracking searches) a too-tight room count produces."""
    demand = num_classes * weekly_periods
    return max(1, math.ceil(demand / (LESSON_SLOTS_PER_WEEK * ROOM_UTILIZATION_TARGET)))


def _weekly_periods_for_capability(capability: str) -> int:
    return next(wp for _, _, wp, cap in SUBJECT_CATALOG if cap == capability)


def _build_rooms(school_id: str, num_classes: int) -> list[Room]:
    num_chem = _rooms_needed_for(num_classes, _weekly_periods_for_capability("CHEMISTRY_LAB"))
    num_gym = _rooms_needed_for(num_classes, _weekly_periods_for_capability("GYM"))
    num_cs = _rooms_needed_for(num_classes, _weekly_periods_for_capability("COMPUTER_LAB"))
    rooms = [
        Room(
            id=f"room_chem_{i}",
            school_id=school_id,
            name=f"Chemistry Lab {i}",
            capacity=32,
            room_type="LABORATORY",
            capabilities=frozenset({"CHEMISTRY_LAB"}),
        )
        for i in range(num_chem)
    ]
    rooms += [
        Room(
            id=f"room_gym_{i}",
            school_id=school_id,
            name=f"Gym {i}",
            capacity=60,
            room_type="GYM",
            capabilities=frozenset({"GYM"}),
        )
        for i in range(num_gym)
    ]
    rooms += [
        Room(
            id=f"room_cs_{i}",
            school_id=school_id,
            name=f"Computer Lab {i}",
            capacity=32,
            room_type="COMPUTER_LAB",
            capabilities=frozenset({"COMPUTER_LAB"}),
        )
        for i in range(num_cs)
    ]
    # Enough plain classrooms that every class can have a distinct room at
    # any single time slot (any room is eligible for a non-capability
    # lesson, so specialized rooms count toward this pool too).
    num_standard = max(0, num_classes - (num_chem + num_gym + num_cs))
    rooms += [
        Room(
            id=f"room_std_{i}",
            school_id=school_id,
            name=f"Room {100 + i}",
            capacity=32,
            room_type="STANDARD",
        )
        for i in range(num_standard)
    ]
    return rooms


def _build_requirements(school_id: str, classes: list[Class]) -> list[LessonRequirement]:
    requirements = []
    for class_ in classes:
        for subject_code, _, weekly_periods, required_capability in SUBJECT_CATALOG:
            requirements.append(
                LessonRequirement(
                    id=f"req_{class_.id}_{subject_code}",
                    school_id=school_id,
                    class_id=class_.id,
                    subject_id=subject_code,
                    weekly_periods=weekly_periods,
                    required_capability=required_capability,
                )
            )
    return requirements


PREFERENCE_RATE = 0.15


def _build_availability(
    school_id: str,
    teachers: list[Teacher],
    days: list[SchoolDay],
    periods: list[TimePeriod],
    rng: random.Random,
) -> list[Availability]:
    lesson_periods = [p for p in periods if p.kind is TimePeriodKind.LESSON]
    records = []
    counter = 0
    for teacher in teachers:
        # Hard unavailability (HC-005), day-independent (a generic
        # "never period X" pattern).
        for period in lesson_periods:
            if rng.random() < UNAVAILABILITY_RATE:
                records.append(
                    Availability(
                        id=f"avail_{counter}",
                        school_id=school_id,
                        owner_type=OwnerType.TEACHER,
                        owner_id=teacher.id,
                        time_period_id=period.id,
                        is_available=False,
                    )
                )
                counter += 1
        # Soft preferences: a day-independent "I generally like/dislike
        # period X" (SC-001) plus a handful of day-specific overrides
        # (SC-002) — see docs/04-DESIGN.md #2, Availability.
        for period in lesson_periods:
            if rng.random() < PREFERENCE_RATE:
                records.append(
                    Availability(
                        id=f"avail_{counter}",
                        school_id=school_id,
                        owner_type=OwnerType.TEACHER,
                        owner_id=teacher.id,
                        time_period_id=period.id,
                        is_available=True,
                        preference_weight=rng.choice([-1.0, 1.0]),
                    )
                )
                counter += 1
        for day in days:
            for period in lesson_periods:
                if rng.random() < PREFERENCE_RATE / 2:
                    records.append(
                        Availability(
                            id=f"avail_{counter}",
                            school_id=school_id,
                            owner_type=OwnerType.TEACHER,
                            owner_id=teacher.id,
                            time_period_id=period.id,
                            day_id=day.id,
                            is_available=True,
                            preference_weight=rng.choice([-1.0, 1.0]),
                        )
                    )
                    counter += 1
    return records


def build_scenario(
    name: str, num_classes: int, *, seed: int = 42, timeout_seconds: float = 60.0
) -> Scenario:
    school_id = f"school_{name}"
    rng = random.Random(seed)

    school = School(id=school_id, name=f"{name.title()} Demo School", timezone="Asia/Jerusalem")
    days, periods = _build_days_and_periods(school_id)
    rooms = _build_rooms(school_id, num_classes)
    standard_room_ids = [r.id for r in rooms if r.room_type == "STANDARD"]
    classes = _build_classes(school_id, num_classes, standard_room_ids, rng)
    teachers = _build_teachers(school_id, num_classes, rng)
    requirements = _build_requirements(school_id, classes)
    availability = _build_availability(school_id, teachers, days, periods, rng)

    problem = build_scheduling_problem(
        school_id,
        teachers=teachers,
        classes=classes,
        rooms=rooms,
        requirements=requirements,
        availability=availability,
        school_days=days,
        time_periods=periods,
        config=SchedulingConfig(timeout_seconds=timeout_seconds, random_seed=seed),
    )
    return Scenario(
        name=name,
        school=school,
        problem=problem,
        school_days=tuple(days),
        time_periods=tuple(periods),
    )


def small_scenario(**kwargs: object) -> Scenario:
    return build_scenario("small", num_classes=5, **kwargs)  # type: ignore[arg-type]


def medium_scenario(**kwargs: object) -> Scenario:
    return build_scenario("medium", num_classes=20, **kwargs)  # type: ignore[arg-type]


def large_scenario(**kwargs: object) -> Scenario:
    return build_scenario("large", num_classes=50, **kwargs)  # type: ignore[arg-type]
