"""SC-004, SC-005: distribute a subject's weekly lessons across the week
rather than clustering them, and avoid excessive consecutive same-subject
lessons for a class (docs/02-PRD.md #18).

Decision: `Subject.max_daily_occurrences`/`min_spacing_days`
(docs/04-DESIGN.md #2) are not read here — wiring per-subject configured
thresholds would require adding `Subject` to `SchedulingProblem`, which
carries no Subject data today (`LessonRequirement` is self-contained and
was sufficient through Phase 4). A fixed, documented threshold is used
instead; per-subject thresholds are a well-scoped follow-up for whichever
phase first threads `Subject` through the scheduling problem (naturally,
once an application layer loads them anyway), not built speculatively now.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.score import PenaltyContribution
from app.domain.models.lesson import Lesson, LessonRequirement
from app.domain.models.school import TimePeriod

if TYPE_CHECKING:
    from app.domain.scheduling.state import ScheduleState

MAX_CONSECUTIVE_SAME_SUBJECT = 2


@dataclass(frozen=True, slots=True)
class SubjectDistributionConstraint:
    id: ClassVar[str] = "SC-004"

    weight: float
    lessons: Sequence[Lesson]
    _requirement_id_by_lesson_id: dict[str, str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_requirement_id_by_lesson_id",
            {lesson.id: lesson.requirement_id for lesson in self.lessons},
        )

    def _clustering_by_requirement(self, state: ScheduleState) -> dict[str, int]:
        days_by_requirement: dict[str, set[str]] = {}
        counts_by_requirement: dict[str, int] = {}
        for assignment in state.assignments:
            requirement_id = self._requirement_id_by_lesson_id.get(assignment.lesson_id)
            if requirement_id is None:
                continue
            days_by_requirement.setdefault(requirement_id, set()).add(assignment.time_slot.day_id)
            counts_by_requirement[requirement_id] = counts_by_requirement.get(requirement_id, 0) + 1

        return {
            requirement_id: count - len(days_by_requirement[requirement_id])
            for requirement_id, count in counts_by_requirement.items()
            if count - len(days_by_requirement[requirement_id]) > 0
        }

    def penalty(self, state: ScheduleState) -> float:
        return float(sum(self._clustering_by_requirement(state).values()))

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        return [
            PenaltyContribution(
                constraint_id=self.id,
                weight=self.weight,
                raw_penalty=float(extra),
                weighted_penalty=self.weight * extra,
                message=f"Requirement {requirement_id} has {extra} lesson(s) sharing a day "
                "with another lesson of the same requirement",
            )
            for requirement_id, extra in self._clustering_by_requirement(state).items()
        ]


@dataclass(frozen=True, slots=True)
class ConsecutiveLessonConstraint:
    id: ClassVar[str] = "SC-005"

    weight: float
    lessons: Sequence[Lesson]
    requirements: Sequence[LessonRequirement]
    time_periods: Sequence[TimePeriod]
    _subject_by_lesson_id: dict[str, str] = field(init=False, repr=False, compare=False)
    _index_by_period_id: dict[str, int] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        requirement_by_id = {r.id: r for r in self.requirements}
        object.__setattr__(
            self,
            "_subject_by_lesson_id",
            {
                lesson.id: requirement_by_id[lesson.requirement_id].subject_id
                for lesson in self.lessons
                if lesson.requirement_id in requirement_by_id
            },
        )
        object.__setattr__(self, "_index_by_period_id", {p.id: p.index for p in self.time_periods})

    def _overrun_by_class(self, state: ScheduleState) -> dict[str, int]:
        by_class_day: dict[tuple[str, str], list[tuple[int, str]]] = {}
        for assignment in state.assignments:
            index = self._index_by_period_id.get(assignment.time_slot.time_period_id)
            subject_id = self._subject_by_lesson_id.get(assignment.lesson_id)
            if index is None or subject_id is None:
                continue
            key = (assignment.class_id, assignment.time_slot.day_id)
            by_class_day.setdefault(key, []).append((index, subject_id))

        overrun: dict[str, int] = {}
        for (class_id, _day_id), entries in by_class_day.items():
            entries.sort()
            run_subject: str | None = None
            run_length = 0
            prev_index: int | None = None
            for index, subject_id in entries:
                if subject_id == run_subject and prev_index is not None and index == prev_index + 1:
                    run_length += 1
                else:
                    run_subject, run_length = subject_id, 1
                if run_length > MAX_CONSECUTIVE_SAME_SUBJECT:
                    overrun[class_id] = overrun.get(class_id, 0) + 1
                prev_index = index
        return overrun

    def penalty(self, state: ScheduleState) -> float:
        return float(sum(self._overrun_by_class(state).values()))

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        return [
            PenaltyContribution(
                constraint_id=self.id,
                weight=self.weight,
                raw_penalty=float(count),
                weighted_penalty=self.weight * count,
                message=f"Class {class_id} has {count} period(s) beyond "
                f"{MAX_CONSECUTIVE_SAME_SUBJECT} consecutive same-subject lessons",
            )
            for class_id, count in self._overrun_by_class(state).items()
        ]
