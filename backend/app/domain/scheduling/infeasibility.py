"""InfeasibilityAnalyzer (docs/04-DESIGN.md #19): explains *why* a schedule
couldn't be completed instead of just returning INFEASIBLE (PRD FR-025,
master prompt §22 — "No valid schedule exists" is never the whole message).

This is a best-effort diagnostic, not a rigorous feasibility proof: each
lesson's `available` count is an optimistic upper bound (it doesn't account
for two lessons in the same bottleneck group competing for the very same
slot), so a reported shortage is a strong signal, not a certainty, and the
converse (no reported shortage) doesn't guarantee a solution exists.
"""

from dataclasses import dataclass, field

from app.domain.models.lesson import Lesson
from app.domain.scheduling.problem import SchedulingProblem
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE, ScheduleState


@dataclass(frozen=True, slots=True)
class BottleneckReport:
    subject_id: str
    required_capability: str | None
    required: int
    available: int
    affected_class_ids: tuple[str, ...]
    affected_teacher_ids: tuple[str, ...]

    @property
    def shortage(self) -> int:
        return max(0, self.required - self.available)


@dataclass(frozen=True, slots=True)
class InfeasibilityResult:
    """`note` is set when the search exhausted every option but no
    single-resource bottleneck explains it — e.g. an interaction between
    two otherwise-fine requirement groups that only conflict in
    combination. `bottlenecks` only groups by (subject, capability), so it
    can miss these."""

    bottlenecks: tuple[BottleneckReport, ...] = field(default_factory=tuple)
    note: str | None = None

    @property
    def is_infeasible(self) -> bool:
        return len(self.bottlenecks) > 0 or self.note is not None


@dataclass(frozen=True, slots=True)
class InfeasibilityAnalyzer:
    problem: SchedulingProblem

    def analyze(self, state: ScheduleState = EMPTY_SCHEDULE_STATE) -> InfeasibilityResult:
        placed_lesson_ids = {a.lesson_id for a in state.assignments}
        unplaced = [lesson for lesson in self.problem.lessons if lesson.id not in placed_lesson_ids]

        groups: dict[tuple[str, str | None], list[Lesson]] = {}
        for lesson in unplaced:
            requirement = self.problem.requirement_by_id[lesson.requirement_id]
            key = (requirement.subject_id, requirement.required_capability)
            groups.setdefault(key, []).append(lesson)

        reports = []
        for (subject_id, required_capability), group_lessons in groups.items():
            available_total = sum(
                self._count_available_slots(lesson, state) for lesson in group_lessons
            )
            required_total = len(group_lessons)
            if required_total > available_total:
                requirement_ids = {
                    self.problem.requirement_by_id[lesson.requirement_id]
                    for lesson in group_lessons
                }
                affected_teachers = self.problem.eligible_teachers_for(next(iter(requirement_ids)))
                reports.append(
                    BottleneckReport(
                        subject_id=subject_id,
                        required_capability=required_capability,
                        required=required_total,
                        available=available_total,
                        affected_class_ids=tuple(sorted({req.class_id for req in requirement_ids})),
                        affected_teacher_ids=tuple(t.id for t in affected_teachers),
                    )
                )

        reports.sort(key=lambda r: r.shortage, reverse=True)
        return InfeasibilityResult(bottlenecks=tuple(reports))

    def _count_available_slots(self, lesson: Lesson, state: ScheduleState) -> int:
        requirement = self.problem.requirement_by_id[lesson.requirement_id]
        class_ = self.problem.class_by_id.get(requirement.class_id)
        if class_ is None:
            return 0
        eligible_teachers = self.problem.eligible_teachers_for(requirement)
        eligible_rooms = self.problem.eligible_rooms_for(requirement, class_)

        count = 0
        for time_slot in self.problem.time_slots:
            if not self.problem.class_available(class_.id, time_slot):
                continue
            if state.class_assignment_at(class_.id, time_slot) is not None:
                continue
            has_free_teacher = any(
                self.problem.teacher_available(teacher.id, time_slot)
                and state.teacher_assignment_at(teacher.id, time_slot) is None
                for teacher in eligible_teachers
            )
            has_free_room = any(
                state.room_assignment_at(room.id, time_slot) is None for room in eligible_rooms
            )
            if has_free_teacher and has_free_room:
                count += 1
        return count
