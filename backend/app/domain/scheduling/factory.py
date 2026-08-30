"""build_scheduling_problem: assembles a `SchedulingProblem` from raw
catalog data (docs/04-DESIGN.md #9, #32 Factory pattern).

The one place that wires concrete constraint instances to catalog data.
Used by both `scripts/scenario_factory.py` (synthetic benchmark/demo
scenarios) and `GenerateScheduleUseCase` (real school data from
Firestore/fakes) so the two can never drift into two different definitions
of "what constraints does a generation run enforce" (docs/01-CLAUDE.md rule
8: hard constraints are never bypassed, and there is exactly one
implementation of what they are).
"""

from collections.abc import Sequence

# Imported from each constraint's own submodule, not the aggregate
# `app.domain.constraints` package `__init__.py` — this module is reached
# (via `app.domain.scheduling.__init__`) from code that imports
# `app.domain.constraints` FIRST (e.g. `tests/domain/scheduling/conftest.py`),
# which starts executing that package's `__init__.py`, which itself imports
# `app.domain.constraints.availability`, which imports
# `app.domain.scheduling.candidate` — re-entering this package while
# `constraints/__init__.py` is still mid-execution. Asking that (still
# partial) package object for names it hasn't bound yet
# (`from app.domain.constraints import BreakConstraint`) raises
# `ImportError: cannot import name ... from partially initialized module`;
# importing directly from each constraint's own submodule sidesteps the
# partially-initialized package namespace entirely and has always worked
# regardless of which package a caller happens to import first.
from app.domain.constraints.availability import (
    ClassAvailabilityConstraint,
    TeacherAvailabilityConstraint,
)
from app.domain.constraints.break_constraint import BreakConstraint
from app.domain.constraints.conflict import (
    ClassConflictConstraint,
    RoomConflictConstraint,
    TeacherConflictConstraint,
)
from app.domain.constraints.distribution import (
    ConsecutiveLessonConstraint,
    SubjectDistributionConstraint,
)
from app.domain.constraints.home_room import HomeRoomPreferenceConstraint
from app.domain.constraints.preferences import (
    TeacherPreferredDayConstraint,
    TeacherPreferredPeriodConstraint,
)
from app.domain.constraints.room_capability import RoomCapabilityConstraint
from app.domain.constraints.room_capacity import RoomCapacityConstraint
from app.domain.constraints.teacher_gap import TeacherGapConstraint
from app.domain.constraints.utilization import ResourceUtilizationConstraint
from app.domain.constraints.workload_balance import ClassWorkloadBalanceConstraint
from app.domain.models.availability import Availability
from app.domain.models.class_ import Class
from app.domain.models.lesson import LessonRequirement
from app.domain.models.room import Room
from app.domain.models.school import SchoolDay, TimePeriod
from app.domain.models.teacher import Teacher
from app.domain.scheduling.problem import SchedulingConfig, SchedulingProblem, build_time_slots


def build_scheduling_problem(
    school_id: str,
    *,
    teachers: Sequence[Teacher],
    classes: Sequence[Class],
    rooms: Sequence[Room],
    requirements: Sequence[LessonRequirement],
    availability: Sequence[Availability],
    school_days: Sequence[SchoolDay],
    time_periods: Sequence[TimePeriod],
    config: SchedulingConfig | None = None,
) -> SchedulingProblem:
    resolved_config = config or SchedulingConfig()
    weights = resolved_config.soft_constraint_weights

    lessons = [lesson for requirement in requirements for lesson in requirement.expand()]
    time_slots = build_time_slots(school_days, time_periods)

    hard_constraints = (
        TeacherConflictConstraint(),
        ClassConflictConstraint(),
        RoomConflictConstraint(),
        RoomCapabilityConstraint(lessons=lessons, requirements=requirements, rooms=rooms),
        TeacherAvailabilityConstraint(availability_records=availability),
        ClassAvailabilityConstraint(availability_records=availability),
        BreakConstraint(time_periods=time_periods),
        RoomCapacityConstraint(classes=classes, rooms=rooms),
    )
    # SC-009/SC-010 (baseline-deviation constraints) are omitted here: a
    # fresh generation run has no prior version to compare against — they
    # belong to rescheduling/regeneration (Phase 9), not initial generation.
    soft_constraints = (
        TeacherPreferredPeriodConstraint(
            weight=weights["SC-001"], availability_records=availability
        ),
        TeacherPreferredDayConstraint(weight=weights["SC-002"], availability_records=availability),
        TeacherGapConstraint(weight=weights["SC-003"], time_periods=time_periods),
        SubjectDistributionConstraint(weight=weights["SC-004"], lessons=lessons),
        ConsecutiveLessonConstraint(
            weight=weights["SC-005"],
            lessons=lessons,
            requirements=requirements,
            time_periods=time_periods,
        ),
        ClassWorkloadBalanceConstraint(
            weight=weights["SC-006"],
            active_day_ids=[day.id for day in school_days if day.is_active],
        ),
        HomeRoomPreferenceConstraint(
            weight=weights["SC-007"], classes=classes, lessons=lessons, requirements=requirements
        ),
        ResourceUtilizationConstraint(weight=weights["SC-008"], rooms=rooms, time_slots=time_slots),
    )

    return SchedulingProblem(
        school_id=school_id,
        lessons=tuple(lessons),
        requirements=tuple(requirements),
        time_slots=time_slots,
        teachers=tuple(teachers),
        classes=tuple(classes),
        rooms=tuple(rooms),
        availability=tuple(availability),
        hard_constraints=hard_constraints,
        soft_constraints=soft_constraints,
        config=resolved_config,
    )
