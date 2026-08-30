"""Domain entities and value objects (docs/04-DESIGN.md #1-3).

Pure Python dataclasses with no dependency on FastAPI or Firebase
(docs/01-CLAUDE.md rules 2-3, NFR-005).
"""

from app.domain.models.audit import Actor, AuditEvent
from app.domain.models.availability import Availability
from app.domain.models.class_ import Class
from app.domain.models.enums import (
    AuditEntityType,
    AuditOperation,
    OwnerType,
    ReschedulingEventType,
    RoomStatus,
    ScheduleVersionStatus,
    TimePeriodKind,
    UserRole,
    Weekday,
)
from app.domain.models.lesson import Lesson, LessonRequirement
from app.domain.models.rescheduling import ReschedulingEvent
from app.domain.models.room import Room
from app.domain.models.schedule import (
    Schedule,
    ScheduleAssignment,
    ScheduleScoreSummary,
    ScheduleVersion,
)
from app.domain.models.school import Break, School, SchoolDay, TimePeriod
from app.domain.models.subject import Subject
from app.domain.models.teacher import Teacher
from app.domain.models.user import User
from app.domain.models.value_objects import TimeSlot
from app.domain.models.verification import EmailVerification

__all__ = [
    "Actor",
    "AuditEntityType",
    "AuditEvent",
    "AuditOperation",
    "Availability",
    "Break",
    "Class",
    "EmailVerification",
    "Lesson",
    "LessonRequirement",
    "OwnerType",
    "ReschedulingEvent",
    "ReschedulingEventType",
    "Room",
    "RoomStatus",
    "Schedule",
    "ScheduleAssignment",
    "ScheduleScoreSummary",
    "ScheduleVersion",
    "ScheduleVersionStatus",
    "School",
    "SchoolDay",
    "Subject",
    "Teacher",
    "TimePeriod",
    "TimePeriodKind",
    "TimeSlot",
    "User",
    "UserRole",
    "Weekday",
]
