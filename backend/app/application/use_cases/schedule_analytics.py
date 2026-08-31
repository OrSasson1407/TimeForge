"""ScheduleAnalyticsUseCase: the read-only management reporting layer over
a schedule version — teacher workload balance, room utilization, and
per-class coverage.

Every figure here is DERIVED from the persisted assignments plus the
catalog, never separately stored. That matters: a stored metric can drift
out of sync with the schedule it describes (the exact failure mode
`ScheduleVersionRepository.update_score` exists to avoid for the score), and
these are read often but change only when the schedule does.

Deliberately not a second scoring implementation: soft-constraint penalties
and the quality figure remain `ConstraintEvaluator`'s job (docs/01-CLAUDE.md
rule 8). What this adds is the *distributional* view the evaluator has no
reason to compute — "is the load spread fairly across teachers", "which
rooms sit empty" — which is a reporting question, not a constraint one.
"""

from dataclasses import dataclass, field
from statistics import pstdev

from app.application.repositories import (
    ClassRepository,
    LessonRequirementRepository,
    RoomRepository,
    ScheduleVersionRepository,
    SchoolDayRepository,
    TeacherRepository,
    TimePeriodRepository,
)
from app.domain.models.enums import RoomStatus, TimePeriodKind


@dataclass(frozen=True, slots=True)
class TeacherWorkload:
    teacher_id: str
    teacher_name: str
    assigned_periods: int
    max_weekly_load: int

    @property
    def load_ratio(self) -> float:
        """Share of the teacher's own contracted maximum that is used. 0.0
        when the maximum is 0 (an unusable configuration, but not this
        module's place to reject)."""
        if self.max_weekly_load <= 0:
            return 0.0
        return self.assigned_periods / self.max_weekly_load


@dataclass(frozen=True, slots=True)
class RoomUtilization:
    room_id: str
    room_name: str
    used_slots: int
    available_slots: int

    @property
    def utilization_ratio(self) -> float:
        if self.available_slots <= 0:
            return 0.0
        return self.used_slots / self.available_slots


@dataclass(frozen=True, slots=True)
class ClassCoverage:
    """Scheduled vs required weekly periods. `required` comes from the
    LessonRequirements, so a shortfall means the version does not fully
    satisfy the curriculum — which a DRAFT legitimately may not."""

    class_id: str
    class_name: str
    scheduled_periods: int
    required_periods: int

    @property
    def is_complete(self) -> bool:
        return self.scheduled_periods >= self.required_periods


@dataclass(frozen=True, slots=True)
class ScheduleAnalytics:
    total_assignments: int
    lesson_slots_per_week: int
    teacher_workloads: tuple[TeacherWorkload, ...] = field(default_factory=tuple)
    room_utilizations: tuple[RoomUtilization, ...] = field(default_factory=tuple)
    class_coverages: tuple[ClassCoverage, ...] = field(default_factory=tuple)

    @property
    def workload_spread(self) -> float:
        """Population standard deviation of assigned periods across
        teachers — the single number that answers "is this schedule fair?".
        0.0 means a perfectly even split; it rises as some teachers carry
        materially more than others."""
        if len(self.teacher_workloads) < 2:
            return 0.0
        return pstdev([w.assigned_periods for w in self.teacher_workloads])


@dataclass(frozen=True, slots=True)
class ScheduleAnalyticsUseCase:
    schedule_version_repository: ScheduleVersionRepository
    teacher_repository: TeacherRepository
    class_repository: ClassRepository
    room_repository: RoomRepository
    requirement_repository: LessonRequirementRepository
    school_day_repository: SchoolDayRepository
    time_period_repository: TimePeriodRepository

    def execute(self, school_id: str, schedule_id: str, version_id: str) -> ScheduleAnalytics:
        assignments = self.schedule_version_repository.list_assignments(schedule_id, version_id)
        teachers = self.teacher_repository.list(school_id)
        classes = self.class_repository.list(school_id)
        rooms = self.room_repository.list(school_id)
        requirements = self.requirement_repository.list(school_id)
        days = self.school_day_repository.list(school_id)
        periods = self.time_period_repository.list(school_id)

        # The denominator for utilization: only ACTIVE days and LESSON
        # periods are schedulable at all, so counting breaks or inactive
        # days would understate every room's utilization.
        active_days = sum(1 for day in days if day.is_active)
        lesson_periods = sum(1 for period in periods if period.kind is TimePeriodKind.LESSON)
        lesson_slots_per_week = active_days * lesson_periods

        periods_by_teacher: dict[str, int] = {}
        slots_by_room: dict[str, int] = {}
        periods_by_class: dict[str, int] = {}
        for assignment in assignments:
            periods_by_teacher[assignment.teacher_id] = (
                periods_by_teacher.get(assignment.teacher_id, 0) + 1
            )
            slots_by_room[assignment.room_id] = slots_by_room.get(assignment.room_id, 0) + 1
            periods_by_class[assignment.class_id] = periods_by_class.get(assignment.class_id, 0) + 1

        required_by_class: dict[str, int] = {}
        for requirement in requirements:
            required_by_class[requirement.class_id] = (
                required_by_class.get(requirement.class_id, 0) + requirement.weekly_periods
            )

        return ScheduleAnalytics(
            total_assignments=len(assignments),
            lesson_slots_per_week=lesson_slots_per_week,
            teacher_workloads=tuple(
                TeacherWorkload(
                    teacher_id=teacher.id,
                    teacher_name=teacher.name,
                    assigned_periods=periods_by_teacher.get(teacher.id, 0),
                    max_weekly_load=teacher.max_weekly_load,
                )
                for teacher in sorted(teachers, key=lambda t: t.name)
            ),
            room_utilizations=tuple(
                RoomUtilization(
                    room_id=room.id,
                    room_name=room.name,
                    used_slots=slots_by_room.get(room.id, 0),
                    # A CLOSED room offers no slots at all; reporting it at
                    # 0/N would read as "badly underused" rather than
                    # "deliberately unavailable".
                    available_slots=(
                        lesson_slots_per_week if room.status is RoomStatus.ACTIVE else 0
                    ),
                )
                for room in sorted(rooms, key=lambda r: r.name)
            ),
            class_coverages=tuple(
                ClassCoverage(
                    class_id=class_.id,
                    class_name=class_.name,
                    scheduled_periods=periods_by_class.get(class_.id, 0),
                    required_periods=required_by_class.get(class_.id, 0),
                )
                for class_ in sorted(classes, key=lambda c: c.name)
            ),
        )
