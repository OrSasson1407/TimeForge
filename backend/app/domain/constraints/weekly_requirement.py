"""HC-008: every lesson requirement's weekly period count must be fully
satisfied in a VALID schedule (docs/02-PRD.md #17).

Unlike HC-001..007/009, this is not a per-candidate conflict check: adding
one more non-conflicting placement can never, by itself, reduce how many of
a requirement's lessons are placed. `is_satisfied` is therefore always
True — this constraint's real content is `violations_in`, a whole-state
completeness check used to validate an already-built (or externally
constructed) schedule, e.g. by the invariant/property tests in
docs/02-PRD.md #17. A solver's own SUCCESS result satisfies this by
construction, since backtracking only returns SUCCESS once every lesson is
placed (docs/04-DESIGN.md #15) — this constraint exists to make that
property independently checkable and testable, per the master prompt's
explicit requirement.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from app.domain.constraints.violation import Severity, Violation
from app.domain.models.lesson import Lesson, LessonRequirement

if TYPE_CHECKING:
    from app.domain.scheduling.candidate import CandidateAssignment
    from app.domain.scheduling.state import ScheduleState


@dataclass(frozen=True, slots=True)
class WeeklyRequirementConstraint:
    id: ClassVar[str] = "HC-008"

    lessons: Sequence[Lesson]
    requirements: Sequence[LessonRequirement]
    _lesson_ids_by_requirement_id: dict[str, frozenset[str]] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        by_requirement: dict[str, set[str]] = {}
        for lesson in self.lessons:
            by_requirement.setdefault(lesson.requirement_id, set()).add(lesson.id)
        object.__setattr__(
            self,
            "_lesson_ids_by_requirement_id",
            {req_id: frozenset(ids) for req_id, ids in by_requirement.items()},
        )

    def is_satisfied(self, state: ScheduleState, candidate: CandidateAssignment) -> bool:
        return True

    def explain_violation(self, state: ScheduleState, candidate: CandidateAssignment) -> Violation:
        raise NotImplementedError(
            "WeeklyRequirementConstraint.is_satisfied is always True; "
            "use violations_in() to check whole-state completeness"
        )

    def violations_in(self, state: ScheduleState) -> list[Violation]:
        placed_lesson_ids = {a.lesson_id for a in state.assignments}
        violations = []
        for requirement in self.requirements:
            required_lesson_ids = self._lesson_ids_by_requirement_id.get(
                requirement.id, frozenset()
            )
            missing = required_lesson_ids - placed_lesson_ids
            if missing:
                violations.append(
                    Violation(
                        constraint_id=self.id,
                        severity=Severity.ERROR,
                        message=f"Requirement {requirement.id} is missing {len(missing)} of "
                        f"{requirement.weekly_periods} weekly periods",
                        involved_entities=(
                            requirement.id,
                            requirement.class_id,
                            requirement.subject_id,
                        ),
                    )
                )
        return violations
