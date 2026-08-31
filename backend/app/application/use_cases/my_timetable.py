"""MyTimetableUseCase: the signed-in teacher's own published timetable, in
one request, fully denormalized.

Shaped for a mobile client, and that shape is the whole point. The web app
fetches assignments plus the teacher/class/room catalogs separately and
joins them in the browser, which is fine over a LAN. A phone on a school
corridor's patchy signal is a different problem: five round trips is five
chances to fail, and an id-only payload is useless when the catalog request
is the one that did not arrive. So this returns names, not ids — one
request that is either complete and renderable offline, or absent.

Reads the PUBLISHED version only. A teacher must never see a draft: drafts
are admin working state that may be hard-constraint-violating and is
routinely thrown away (docs/04-DESIGN.md #25).
"""

from dataclasses import dataclass, field
from datetime import time

from app.application.repositories import (
    ClassRepository,
    LessonRequirementRepository,
    RoomRepository,
    ScheduleRepository,
    ScheduleVersionRepository,
    SchoolDayRepository,
    SubjectRepository,
    TimePeriodRepository,
)
from app.domain.models.enums import Weekday


@dataclass(frozen=True, slots=True)
class TimetableEntry:
    assignment_id: str
    day_id: str
    weekday: Weekday
    time_period_id: str
    period_index: int
    start_time: time
    end_time: time
    class_name: str
    room_name: str
    subject_code: str
    subject_name: str


@dataclass(frozen=True, slots=True)
class MyTimetable:
    #: None when the school has never published a schedule, or the teacher
    #: has no assignments in it. The client renders an empty state rather
    #: than an error — "nothing published yet" is a normal state, not a
    #: failure.
    version_id: str | None
    entries: tuple[TimetableEntry, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MyTimetableUseCase:
    schedule_repository: ScheduleRepository
    schedule_version_repository: ScheduleVersionRepository
    class_repository: ClassRepository
    room_repository: RoomRepository
    subject_repository: SubjectRepository
    requirement_repository: LessonRequirementRepository
    school_day_repository: SchoolDayRepository
    time_period_repository: TimePeriodRepository

    def execute(self, school_id: str, teacher_id: str) -> MyTimetable:
        schedule = self.schedule_repository.get(school_id)
        version_id = schedule.active_version_id if schedule else None
        if version_id is None:
            return MyTimetable(version_id=None)

        assignments = [
            assignment
            for assignment in self.schedule_version_repository.list_assignments(
                school_id, version_id
            )
            if assignment.teacher_id == teacher_id
        ]
        if not assignments:
            return MyTimetable(version_id=version_id)

        class_names = {c.id: c.name for c in self.class_repository.list(school_id)}
        room_names = {r.id: r.name for r in self.room_repository.list(school_id)}
        subjects = {s.id: s for s in self.subject_repository.list(school_id)}
        days = {d.id: d for d in self.school_day_repository.list(school_id)}
        periods = {p.id: p for p in self.time_period_repository.list(school_id)}

        # Lessons are derived, never stored (LessonRequirement.expand), so
        # the lesson -> subject link is rebuilt the same way the solver
        # builds it rather than by parsing the lesson id, which only looks
        # like it encodes the requirement.
        requirements = self.requirement_repository.list(school_id)
        subject_id_by_lesson_id = {
            lesson.id: requirement.subject_id
            for requirement in requirements
            for lesson in requirement.expand()
        }

        entries = []
        for assignment in assignments:
            day = days.get(assignment.day_id)
            period = periods.get(assignment.time_period_id)
            if day is None or period is None:
                # The catalog no longer contains this slot (a day or period
                # deleted after publication). Skipping is the honest
                # response: the entry cannot be placed on a grid, and
                # inventing a placeholder time would be worse than omitting
                # a lesson the school has already stopped running.
                continue
            subject_id = subject_id_by_lesson_id.get(assignment.lesson_id, "")
            subject = subjects.get(subject_id)
            entries.append(
                TimetableEntry(
                    assignment_id=assignment.id,
                    day_id=day.id,
                    weekday=day.weekday,
                    time_period_id=period.id,
                    period_index=period.index,
                    start_time=period.start_time,
                    end_time=period.end_time,
                    class_name=class_names.get(assignment.class_id, assignment.class_id),
                    room_name=room_names.get(assignment.room_id, assignment.room_id),
                    subject_code=subject.code if subject else subject_id,
                    subject_name=subject.name if subject else subject_id,
                )
            )

        entries.sort(key=lambda e: (e.period_index, e.day_id))
        return MyTimetable(version_id=version_id, entries=tuple(entries))
