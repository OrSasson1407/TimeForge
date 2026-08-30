"""CompareVersionsUseCase (docs/03-ARCHITECTURE.md #26 `GET
/schedules/{id}/compare`): a pure diff over two versions' assignment sets,
keyed by `lesson_id` (docs/02-PRD.md "change explanations" — the frontend
needs to say what moved, not just that something did).
"""

from dataclasses import dataclass

from app.application.repositories import ScheduleVersionRepository
from app.domain.models import ScheduleAssignment


@dataclass(frozen=True, slots=True)
class AssignmentDiff:
    lesson_id: str
    before: ScheduleAssignment | None = None
    after: ScheduleAssignment | None = None


@dataclass(frozen=True, slots=True)
class CompareVersionsResult:
    from_version_id: str
    to_version_id: str
    added: list[AssignmentDiff]
    removed: list[AssignmentDiff]
    moved: list[AssignmentDiff]
    unchanged_count: int


def _placement(assignment: ScheduleAssignment) -> tuple[str, str, str, str]:
    return (assignment.teacher_id, assignment.room_id, assignment.day_id, assignment.time_period_id)


@dataclass(frozen=True, slots=True)
class CompareVersionsUseCase:
    schedule_version_repository: ScheduleVersionRepository

    def execute(
        self, schedule_id: str, from_version_id: str, to_version_id: str
    ) -> CompareVersionsResult:
        before_by_lesson = {
            a.lesson_id: a
            for a in self.schedule_version_repository.list_assignments(schedule_id, from_version_id)
        }
        after_by_lesson = {
            a.lesson_id: a
            for a in self.schedule_version_repository.list_assignments(schedule_id, to_version_id)
        }

        added: list[AssignmentDiff] = []
        removed: list[AssignmentDiff] = []
        moved: list[AssignmentDiff] = []
        unchanged_count = 0

        for lesson_id in sorted(set(before_by_lesson) | set(after_by_lesson)):
            before = before_by_lesson.get(lesson_id)
            after = after_by_lesson.get(lesson_id)
            if before is None and after is not None:
                added.append(AssignmentDiff(lesson_id=lesson_id, after=after))
            elif before is not None and after is None:
                removed.append(AssignmentDiff(lesson_id=lesson_id, before=before))
            elif before is not None and after is not None:
                if _placement(before) != _placement(after):
                    moved.append(AssignmentDiff(lesson_id=lesson_id, before=before, after=after))
                else:
                    unchanged_count += 1

        return CompareVersionsResult(
            from_version_id=from_version_id,
            to_version_id=to_version_id,
            added=added,
            removed=removed,
            moved=moved,
            unchanged_count=unchanged_count,
        )
