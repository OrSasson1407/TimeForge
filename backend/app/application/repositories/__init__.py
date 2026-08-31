"""Repository interfaces (docs/04-DESIGN.md #7-8): contracts the
application layer depends on and `app.infrastructure.repositories`
implements. Defined here, not in `app.domain`, because the domain layer
never consumes a repository at all (docs/01-CLAUDE.md rules 2-3).
"""

from app.application.repositories.audit import AuditRepository
from app.application.repositories.availability import AvailabilityRepository
from app.application.repositories.catalog import (
    ClassRepository,
    LessonRequirementRepository,
    RoomRepository,
    SchoolDayRepository,
    SubjectRepository,
    TeacherRepository,
    TimePeriodRepository,
)
from app.application.repositories.device import DeviceTokenRepository, PushSenderPort
from app.application.repositories.generic import Repository
from app.application.repositories.identity_admin import IdentityAdminPort
from app.application.repositories.rescheduling import ReschedulingEventRepository
from app.application.repositories.schedule import ScheduleRepository, ScheduleVersionRepository
from app.application.repositories.scheduling_config import SchedulingConfigRepository
from app.application.repositories.school import SchoolRepository
from app.application.repositories.user import UserRepository
from app.application.repositories.verification import VerificationCodeRepository

__all__ = [
    "AuditRepository",
    "AvailabilityRepository",
    "ClassRepository",
    "DeviceTokenRepository",
    "IdentityAdminPort",
    "LessonRequirementRepository",
    "PushSenderPort",
    "ReschedulingEventRepository",
    "Repository",
    "RoomRepository",
    "ScheduleRepository",
    "ScheduleVersionRepository",
    "SchedulingConfigRepository",
    "SchoolDayRepository",
    "SchoolRepository",
    "SubjectRepository",
    "TeacherRepository",
    "TimePeriodRepository",
    "UserRepository",
    "VerificationCodeRepository",
]
