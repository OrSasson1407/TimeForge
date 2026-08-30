"""SC-007: prefer a class's home room when no special capability is
required (docs/02-PRD.md #18) — a capability-driven placement (e.g.
Chemistry needing CHEMISTRY_LAB) is excluded from this preference
entirely, since the class's home room may not even qualify.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.score import PenaltyContribution
from app.domain.models.class_ import Class
from app.domain.models.lesson import Lesson, LessonRequirement

if TYPE_CHECKING:
    from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class HomeRoomPreferenceConstraint:
    id: ClassVar[str] = "SC-007"

    weight: float
    classes: Sequence[Class]
    lessons: Sequence[Lesson]
    requirements: Sequence[LessonRequirement]
    _home_room_by_class_id: dict[str, str] = field(init=False, repr=False, compare=False)
    _requirement_by_lesson_id: dict[str, LessonRequirement] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_home_room_by_class_id",
            {c.id: c.home_room_id for c in self.classes if c.home_room_id},
        )
        requirement_by_id = {r.id: r for r in self.requirements}
        object.__setattr__(
            self,
            "_requirement_by_lesson_id",
            {
                lesson.id: requirement_by_id[lesson.requirement_id]
                for lesson in self.lessons
                if lesson.requirement_id in requirement_by_id
            },
        )

    def _misplacements_by_class(self, state: ScheduleState) -> dict[str, int]:
        counts: dict[str, int] = {}
        for assignment in state.assignments:
            home_room = self._home_room_by_class_id.get(assignment.class_id)
            if home_room is None:
                continue
            requirement = self._requirement_by_lesson_id.get(assignment.lesson_id)
            if requirement is None or requirement.required_capability is not None:
                continue
            if assignment.room_id != home_room:
                counts[assignment.class_id] = counts.get(assignment.class_id, 0) + 1
        return counts

    def penalty(self, state: ScheduleState) -> float:
        return float(sum(self._misplacements_by_class(state).values()))

    def explain(self, state: ScheduleState) -> list[PenaltyContribution]:
        return [
            PenaltyContribution(
                constraint_id=self.id,
                weight=self.weight,
                raw_penalty=float(count),
                weighted_penalty=self.weight * count,
                message=f"Class {class_id} has {count} non-specialized lesson(s) outside its "
                "home room",
            )
            for class_id, count in self._misplacements_by_class(state).items()
        ]
