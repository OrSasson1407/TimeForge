"""Type aliases for the school-scoped catalog/config repositories
(docs/05-DATABASE.md #3) — each is exactly `Repository[T]` (see
`generic.py`); named aliases exist purely for readable type hints at
call sites (e.g. a use case's constructor), not because their shape
differs.
"""

from app.application.repositories.generic import Repository
from app.domain.models import (
    Class,
    LessonRequirement,
    Room,
    SchoolDay,
    Subject,
    Teacher,
    TimePeriod,
)

TeacherRepository = Repository[Teacher]
ClassRepository = Repository[Class]
SubjectRepository = Repository[Subject]
RoomRepository = Repository[Room]
SchoolDayRepository = Repository[SchoolDay]
TimePeriodRepository = Repository[TimePeriod]
LessonRequirementRepository = Repository[LessonRequirement]
