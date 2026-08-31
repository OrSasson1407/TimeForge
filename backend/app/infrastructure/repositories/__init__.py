"""Firestore-backed implementations of the `app.application.repositories`
interfaces (docs/01-CLAUDE.md rule 6: Firestore access is centralized
here — nowhere else in the codebase imports `google.cloud.firestore` or
`firebase_admin.firestore`).
"""

from app.infrastructure.repositories.audit_firestore import FirestoreAuditRepository
from app.infrastructure.repositories.availability_firestore import (
    FirestoreAvailabilityRepository,
)
from app.infrastructure.repositories.catalog_firestore import (
    build_class_repository,
    build_lesson_requirement_repository,
    build_room_repository,
    build_school_day_repository,
    build_subject_repository,
    build_teacher_repository,
    build_time_period_repository,
)
from app.infrastructure.repositories.device_firestore import FirestoreDeviceTokenRepository
from app.infrastructure.repositories.rescheduling_firestore import (
    FirestoreReschedulingEventRepository,
)
from app.infrastructure.repositories.schedule_firestore import (
    FirestoreScheduleRepository,
    FirestoreScheduleVersionRepository,
)
from app.infrastructure.repositories.scheduling_config_firestore import (
    FirestoreSchedulingConfigRepository,
)
from app.infrastructure.repositories.school_firestore import FirestoreSchoolRepository
from app.infrastructure.repositories.user_firestore import FirestoreUserRepository
from app.infrastructure.repositories.verification_firestore import (
    FirestoreVerificationCodeRepository,
)

__all__ = [
    "FirestoreAuditRepository",
    "FirestoreAvailabilityRepository",
    "FirestoreReschedulingEventRepository",
    "FirestoreScheduleRepository",
    "FirestoreSchedulingConfigRepository",
    "FirestoreScheduleVersionRepository",
    "FirestoreSchoolRepository",
    "FirestoreDeviceTokenRepository",
    "FirestoreUserRepository",
    "FirestoreVerificationCodeRepository",
    "build_class_repository",
    "build_lesson_requirement_repository",
    "build_room_repository",
    "build_school_day_repository",
    "build_subject_repository",
    "build_teacher_repository",
    "build_time_period_repository",
]
