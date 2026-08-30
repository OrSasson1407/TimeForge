"""SchedulingProblem (docs/04-DESIGN.md #9): the solver's complete input.

Assembled from raw domain data by a factory step (docs/04-DESIGN.md #32) —
`build_time_slots()` is that factory's one piece of nontrivial logic
(the active-days x lesson-periods cartesian product); everything else is
handed to `SchedulingProblem` already resolved. The problem carries its own
static-eligibility indexes so `candidate_slots_for()`/`resolve_placement()`
can generate a lesson's *statically* legal placements (right
subject-competent teacher, right capability/capacity room, an
available/non-break slot) without walking the full constraint list for
every combination — HC-001/002/003 (the *dynamic* conflicts, which depend
on what's already been placed) are still checked by the shared
ConstraintEvaluator during search, never bypassed.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field

from app.domain.constraints.base import HardConstraint
from app.domain.constraints.soft_base import SoftConstraint
from app.domain.models.availability import Availability, AvailabilityIndex, build_availability_index
from app.domain.models.class_ import Class
from app.domain.models.enums import OwnerType, RoomStatus, TimePeriodKind
from app.domain.models.lesson import Lesson, LessonRequirement
from app.domain.models.room import Room
from app.domain.models.school import SchoolDay, TimePeriod
from app.domain.models.teacher import Teacher
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.candidate import CandidateAssignment
from app.domain.scheduling.state import ScheduleState


def build_time_slots(
    school_days: Sequence[SchoolDay], time_periods: Sequence[TimePeriod]
) -> tuple[TimeSlot, ...]:
    """The cartesian product of active SchoolDays x LESSON-kind TimePeriods
    (docs/04-DESIGN.md #9) — a school's week is never hardcoded (master
    prompt #14), and breaks are excluded at the source rather than merely
    rejected later (HC-007 becomes structurally unreachable for any
    search-generated candidate, though it still guards manual moves)."""
    active_days = [day for day in school_days if day.is_active]
    lesson_periods = [period for period in time_periods if period.kind is TimePeriodKind.LESSON]
    return tuple(
        TimeSlot(day_id=day.id, time_period_id=period.id)
        for day in active_days
        for period in lesson_periods
    )


#: docs/05-DATABASE.md #19 `schedulingConfig` example — the persisted default.
DEFAULT_SOFT_CONSTRAINT_WEIGHTS: dict[str, float] = {
    "SC-001": 1.0,
    "SC-002": 1.0,
    "SC-003": 2.0,
    "SC-004": 1.5,
    "SC-005": 1.5,
    "SC-006": 1.0,
    "SC-007": 0.5,
    "SC-008": 1.0,
    "SC-009": 3.0,
    "SC-010": 2.0,
}


@dataclass(frozen=True, slots=True)
class SchedulingConfig:
    timeout_seconds: float = 60.0
    random_seed: int = 42
    soft_constraint_weights: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_SOFT_CONSTRAINT_WEIGHTS)
    )
    #: docs/04-DESIGN.md #15 SimulatedAnnealingOptimizer parameters.
    initial_temperature: float = 10.0
    cooling_rate: float = 0.995
    min_temperature: float = 0.01
    #: docs/04-DESIGN.md #13 quality formula's decay constant `k`.
    quality_decay_k: float = 0.05

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("SchedulingConfig.timeout_seconds must be > 0")
        if self.initial_temperature <= 0:
            raise ValueError("SchedulingConfig.initial_temperature must be > 0")
        if not (0 < self.cooling_rate < 1):
            raise ValueError("SchedulingConfig.cooling_rate must be in (0, 1)")
        if self.min_temperature <= 0:
            raise ValueError("SchedulingConfig.min_temperature must be > 0")
        if self.min_temperature >= self.initial_temperature:
            raise ValueError("SchedulingConfig.min_temperature must be < initial_temperature")
        if self.quality_decay_k <= 0:
            raise ValueError("SchedulingConfig.quality_decay_k must be > 0")


@dataclass(frozen=True, slots=True)
class SchedulingProblem:
    school_id: str
    lessons: tuple[Lesson, ...]
    requirements: tuple[LessonRequirement, ...]
    time_slots: tuple[TimeSlot, ...]
    teachers: tuple[Teacher, ...]
    classes: tuple[Class, ...]
    rooms: tuple[Room, ...]
    availability: tuple[Availability, ...]
    hard_constraints: tuple[HardConstraint, ...]
    soft_constraints: tuple[SoftConstraint, ...] = field(default_factory=tuple)
    config: SchedulingConfig = field(default_factory=SchedulingConfig)

    requirement_by_id: dict[str, LessonRequirement] = field(init=False, repr=False, compare=False)
    lesson_by_id: dict[str, Lesson] = field(init=False, repr=False, compare=False)
    class_by_id: dict[str, Class] = field(init=False, repr=False, compare=False)
    _teachers_by_subject: dict[str, tuple[Teacher, ...]] = field(
        init=False, repr=False, compare=False
    )
    _teacher_availability: AvailabilityIndex = field(init=False, repr=False, compare=False)
    _class_availability: AvailabilityIndex = field(init=False, repr=False, compare=False)
    _eligible_rooms_cache: dict[tuple[str | None, int], tuple[Room, ...]] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if not self.school_id:
            raise ValueError("SchedulingProblem.school_id must not be empty")

        requirement_by_id = {r.id: r for r in self.requirements}
        missing = [
            lesson.id for lesson in self.lessons if lesson.requirement_id not in requirement_by_id
        ]
        if missing:
            raise ValueError(
                f"SchedulingProblem: lessons reference unknown requirements: {missing}"
            )
        object.__setattr__(self, "requirement_by_id", requirement_by_id)
        object.__setattr__(self, "lesson_by_id", {lesson.id: lesson for lesson in self.lessons})
        object.__setattr__(self, "class_by_id", {c.id: c for c in self.classes})

        teachers_by_subject: dict[str, list[Teacher]] = {}
        for teacher in self.teachers:
            for subject_id in teacher.subject_ids:
                teachers_by_subject.setdefault(subject_id, []).append(teacher)
        object.__setattr__(
            self,
            "_teachers_by_subject",
            {subject_id: tuple(ts) for subject_id, ts in teachers_by_subject.items()},
        )

        object.__setattr__(
            self,
            "_teacher_availability",
            build_availability_index(self.availability, OwnerType.TEACHER),
        )
        object.__setattr__(
            self,
            "_class_availability",
            build_availability_index(self.availability, OwnerType.CLASS),
        )
        object.__setattr__(self, "_eligible_rooms_cache", {})

    def teacher_available(self, teacher_id: str, time_slot: TimeSlot) -> bool:
        return self._teacher_availability.is_available(
            teacher_id, time_slot.day_id, time_slot.time_period_id
        )

    def class_available(self, class_id: str, time_slot: TimeSlot) -> bool:
        return self._class_availability.is_available(
            class_id, time_slot.day_id, time_slot.time_period_id
        )

    def eligible_teachers_for(self, requirement: LessonRequirement) -> tuple[Teacher, ...]:
        return self._teachers_by_subject.get(requirement.subject_id, ())

    def eligible_rooms_for(self, requirement: LessonRequirement, class_: Class) -> tuple[Room, ...]:
        """Memoized: only `required_capability` and `student_count` affect
        the result, so many (requirement, class) pairs share a cache entry.
        Without this, a full O(rooms) scan re-ran on every call — including
        from inside `resolve_placement`'s per-teacher loop — which was the
        dominant cost in the "Large" benchmark scenario
        (docs/03-ARCHITECTURE.md #30)."""
        key = (requirement.required_capability, class_.student_count)
        cached = self._eligible_rooms_cache.get(key)
        if cached is not None:
            return cached
        result = tuple(
            room
            for room in self.rooms
            if room.status is RoomStatus.ACTIVE
            and room.can_seat(class_.student_count)
            and (
                requirement.required_capability is None
                or room.has_capability(requirement.required_capability)
            )
        )
        self._eligible_rooms_cache[key] = result
        return result

    def candidate_slots_for(self, lesson: Lesson) -> tuple[TimeSlot, ...]:
        """A lesson's statically-legal time slots: the class is available
        and at least one subject-competent teacher is available.

        Decision: the search's domain is TIME SLOTS, not the full
        (slot x teacher x room) cartesian product — for a lesson with 2
        eligible teachers and 5 eligible rooms across 40 slots, enumerating
        every combination up front produced ~400 domain entries per lesson,
        and forward-checking (which re-validates every remaining lesson's
        full domain at every step) made even the "Small" benchmark scenario
        take >10s despite trivial actual backtracking. `resolve_placement`
        below picks a specific (teacher, room) lazily, only for the slot
        actually being tried, keeping domains bounded by slot count (see
        `resolve_placement`'s docstring for the completeness trade-off this
        implies).
        """
        requirement = self.requirement_by_id[lesson.requirement_id]
        class_ = self.class_by_id.get(requirement.class_id)
        if class_ is None:
            return ()
        eligible_teachers = self.eligible_teachers_for(requirement)
        eligible_rooms = self.eligible_rooms_for(requirement, class_)
        if not eligible_teachers or not eligible_rooms:
            return ()

        return tuple(
            time_slot
            for time_slot in self.time_slots
            if self.class_available(class_.id, time_slot)
            and any(self.teacher_available(teacher.id, time_slot) for teacher in eligible_teachers)
        )

    def resolve_placement(
        self, lesson: Lesson, time_slot: TimeSlot, state: ScheduleState
    ) -> CandidateAssignment | None:
        """The first free (teacher, room) pair for `lesson` at `time_slot`
        given `state` (HC-001/002/003 checked via ScheduleState's O(1)
        indexes) — first-fit, not exhaustive: if this specific pair later
        turns out to be a dead end elsewhere, the search backtracks to a
        *different time slot* for this lesson rather than retrying the same
        slot with a different teacher/room pair. This trades a small,
        theoretical completeness gap (a solution that exists only via a
        non-first resource pick at some slot could be missed) for a large,
        measured performance win, and is bounded in practice by the
        healthy teacher/room margins in `scripts/scenario_factory.py`.
        """
        requirement = self.requirement_by_id[lesson.requirement_id]
        class_ = self.class_by_id.get(requirement.class_id)
        if class_ is None or state.class_assignment_at(class_.id, time_slot) is not None:
            return None

        eligible_rooms = self.eligible_rooms_for(requirement, class_)
        for teacher in self.eligible_teachers_for(requirement):
            if not self.teacher_available(teacher.id, time_slot):
                continue
            if state.teacher_assignment_at(teacher.id, time_slot) is not None:
                continue
            for room in eligible_rooms:
                if state.room_assignment_at(room.id, time_slot) is not None:
                    continue
                return CandidateAssignment(
                    lesson_id=lesson.id,
                    class_id=class_.id,
                    teacher_id=teacher.id,
                    room_id=room.id,
                    time_slot=time_slot,
                )
        return None
