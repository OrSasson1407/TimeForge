"""FastAPI dependency providers (docs/07-CODE_STANDARDS.md #21): repository
instances and authentication/authorization. Every provider is a plain,
importable function so tests can override it via `app.dependency_overrides`
(docs/03-ARCHITECTURE.md #35) — production wiring constructs Firestore-
backed repositories; tests substitute the fakes from
`tests.support.fakes`.
"""

from functools import lru_cache

from fastapi import Depends, Header

from app.application.repositories import (
    AuditRepository,
    AvailabilityRepository,
    ClassRepository,
    IdentityAdminPort,
    LessonRequirementRepository,
    ReschedulingEventRepository,
    RoomRepository,
    ScheduleRepository,
    ScheduleVersionRepository,
    SchedulingConfigRepository,
    SchoolDayRepository,
    SchoolRepository,
    SubjectRepository,
    TeacherRepository,
    TimePeriodRepository,
    UserRepository,
    VerificationCodeRepository,
)
from app.application.use_cases import (
    ApplyMoveUseCase,
    CompareVersionsUseCase,
    GenerateScheduleUseCase,
    PublishScheduleUseCase,
    RescheduleUseCase,
    ValidateMoveUseCase,
)
from app.core.config import get_settings
from app.core.errors import AuthenticationError, AuthorizationError
from app.core.rate_limit import RateLimiter
from app.domain.models import User, UserRole
from app.infrastructure.email import EmailSender, SmtpEmailSender
from app.infrastructure.firebase.auth import FirebaseIdentityAdmin, resolve_user
from app.infrastructure.firebase.client import get_firestore_client
from app.infrastructure.repositories import (
    FirestoreAuditRepository,
    FirestoreAvailabilityRepository,
    FirestoreReschedulingEventRepository,
    FirestoreScheduleRepository,
    FirestoreScheduleVersionRepository,
    FirestoreSchedulingConfigRepository,
    FirestoreSchoolRepository,
    FirestoreUserRepository,
    FirestoreVerificationCodeRepository,
    build_class_repository,
    build_lesson_requirement_repository,
    build_room_repository,
    build_school_day_repository,
    build_subject_repository,
    build_teacher_repository,
    build_time_period_repository,
)

# --- Repository providers (production: Firestore-backed, cached) ---


@lru_cache
def get_school_repository() -> SchoolRepository:
    return FirestoreSchoolRepository(get_firestore_client())


@lru_cache
def get_teacher_repository() -> TeacherRepository:
    return build_teacher_repository(get_firestore_client())


@lru_cache
def get_class_repository() -> ClassRepository:
    return build_class_repository(get_firestore_client())


@lru_cache
def get_subject_repository() -> SubjectRepository:
    return build_subject_repository(get_firestore_client())


@lru_cache
def get_room_repository() -> RoomRepository:
    return build_room_repository(get_firestore_client())


@lru_cache
def get_school_day_repository() -> SchoolDayRepository:
    return build_school_day_repository(get_firestore_client())


@lru_cache
def get_time_period_repository() -> TimePeriodRepository:
    return build_time_period_repository(get_firestore_client())


@lru_cache
def get_lesson_requirement_repository() -> LessonRequirementRepository:
    return build_lesson_requirement_repository(get_firestore_client())


@lru_cache
def get_availability_repository() -> AvailabilityRepository:
    return FirestoreAvailabilityRepository(get_firestore_client())


@lru_cache
def get_scheduling_config_repository() -> SchedulingConfigRepository:
    return FirestoreSchedulingConfigRepository(get_firestore_client())


@lru_cache
def get_schedule_repository() -> ScheduleRepository:
    return FirestoreScheduleRepository(get_firestore_client())


@lru_cache
def get_schedule_version_repository() -> ScheduleVersionRepository:
    return FirestoreScheduleVersionRepository(get_firestore_client())


@lru_cache
def get_audit_repository() -> AuditRepository:
    return FirestoreAuditRepository(get_firestore_client())


@lru_cache
def get_user_repository() -> UserRepository:
    return FirestoreUserRepository(get_firestore_client())


@lru_cache
def get_rescheduling_event_repository() -> ReschedulingEventRepository:
    return FirestoreReschedulingEventRepository(get_firestore_client())


@lru_cache
def get_verification_repository() -> VerificationCodeRepository:
    return FirestoreVerificationCodeRepository(get_firestore_client())


@lru_cache
def get_identity_admin() -> IdentityAdminPort:
    return FirebaseIdentityAdmin()


# --- Registration: email delivery and rate limiting ---


@lru_cache
def get_email_sender() -> EmailSender:
    return SmtpEmailSender(get_settings())


@lru_cache
def get_register_rate_limiter() -> RateLimiter:
    settings = get_settings()
    return RateLimiter(max_calls=settings.register_rate_limit_per_hour, window_seconds=3600)


@lru_cache
def get_resend_code_rate_limiter() -> RateLimiter:
    settings = get_settings()
    return RateLimiter(max_calls=settings.resend_code_rate_limit_per_15min, window_seconds=900)


# --- Authentication / Authorization ---


def extract_bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise AuthenticationError("Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Authorization header must be 'Bearer <token>'")
    return token


def get_current_user(
    token: str = Depends(extract_bearer_token),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    """Verifies the ID token via the Admin SDK and resolves it to the
    backend's own User record — the role always comes from Firestore, not
    from any client-supplied claim (docs/03-ARCHITECTURE.md #23-24)."""
    return resolve_user(token, user_repository)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role is not UserRole.ADMIN:
        raise AuthorizationError("This action requires an administrator")
    return user


# --- Scheduling-workflow use cases ---


def get_generate_schedule_use_case(
    schedule_repository: ScheduleRepository = Depends(get_schedule_repository),
    schedule_version_repository: ScheduleVersionRepository = Depends(
        get_schedule_version_repository
    ),
    teacher_repository: TeacherRepository = Depends(get_teacher_repository),
    class_repository: ClassRepository = Depends(get_class_repository),
    room_repository: RoomRepository = Depends(get_room_repository),
    requirement_repository: LessonRequirementRepository = Depends(
        get_lesson_requirement_repository
    ),
    availability_repository: AvailabilityRepository = Depends(get_availability_repository),
    school_day_repository: SchoolDayRepository = Depends(get_school_day_repository),
    time_period_repository: TimePeriodRepository = Depends(get_time_period_repository),
    scheduling_config_repository: SchedulingConfigRepository = Depends(
        get_scheduling_config_repository
    ),
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> GenerateScheduleUseCase:
    return GenerateScheduleUseCase(
        schedule_repository=schedule_repository,
        schedule_version_repository=schedule_version_repository,
        teacher_repository=teacher_repository,
        class_repository=class_repository,
        room_repository=room_repository,
        requirement_repository=requirement_repository,
        availability_repository=availability_repository,
        school_day_repository=school_day_repository,
        time_period_repository=time_period_repository,
        scheduling_config_repository=scheduling_config_repository,
        audit_repository=audit_repository,
    )


def get_validate_move_use_case(
    schedule_version_repository: ScheduleVersionRepository = Depends(
        get_schedule_version_repository
    ),
    teacher_repository: TeacherRepository = Depends(get_teacher_repository),
    class_repository: ClassRepository = Depends(get_class_repository),
    room_repository: RoomRepository = Depends(get_room_repository),
    requirement_repository: LessonRequirementRepository = Depends(
        get_lesson_requirement_repository
    ),
    availability_repository: AvailabilityRepository = Depends(get_availability_repository),
    school_day_repository: SchoolDayRepository = Depends(get_school_day_repository),
    time_period_repository: TimePeriodRepository = Depends(get_time_period_repository),
    scheduling_config_repository: SchedulingConfigRepository = Depends(
        get_scheduling_config_repository
    ),
) -> ValidateMoveUseCase:
    return ValidateMoveUseCase(
        schedule_version_repository=schedule_version_repository,
        teacher_repository=teacher_repository,
        class_repository=class_repository,
        room_repository=room_repository,
        requirement_repository=requirement_repository,
        availability_repository=availability_repository,
        school_day_repository=school_day_repository,
        time_period_repository=time_period_repository,
        scheduling_config_repository=scheduling_config_repository,
    )


def get_apply_move_use_case(
    schedule_version_repository: ScheduleVersionRepository = Depends(
        get_schedule_version_repository
    ),
    teacher_repository: TeacherRepository = Depends(get_teacher_repository),
    class_repository: ClassRepository = Depends(get_class_repository),
    room_repository: RoomRepository = Depends(get_room_repository),
    requirement_repository: LessonRequirementRepository = Depends(
        get_lesson_requirement_repository
    ),
    availability_repository: AvailabilityRepository = Depends(get_availability_repository),
    school_day_repository: SchoolDayRepository = Depends(get_school_day_repository),
    time_period_repository: TimePeriodRepository = Depends(get_time_period_repository),
    scheduling_config_repository: SchedulingConfigRepository = Depends(
        get_scheduling_config_repository
    ),
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> ApplyMoveUseCase:
    return ApplyMoveUseCase(
        schedule_version_repository=schedule_version_repository,
        teacher_repository=teacher_repository,
        class_repository=class_repository,
        room_repository=room_repository,
        requirement_repository=requirement_repository,
        availability_repository=availability_repository,
        school_day_repository=school_day_repository,
        time_period_repository=time_period_repository,
        scheduling_config_repository=scheduling_config_repository,
        audit_repository=audit_repository,
    )


def get_publish_schedule_use_case(
    schedule_version_repository: ScheduleVersionRepository = Depends(
        get_schedule_version_repository
    ),
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> PublishScheduleUseCase:
    return PublishScheduleUseCase(
        schedule_version_repository=schedule_version_repository, audit_repository=audit_repository
    )


def get_compare_versions_use_case(
    schedule_version_repository: ScheduleVersionRepository = Depends(
        get_schedule_version_repository
    ),
) -> CompareVersionsUseCase:
    return CompareVersionsUseCase(schedule_version_repository=schedule_version_repository)


def get_reschedule_use_case(
    schedule_repository: ScheduleRepository = Depends(get_schedule_repository),
    schedule_version_repository: ScheduleVersionRepository = Depends(
        get_schedule_version_repository
    ),
    rescheduling_event_repository: ReschedulingEventRepository = Depends(
        get_rescheduling_event_repository
    ),
    teacher_repository: TeacherRepository = Depends(get_teacher_repository),
    class_repository: ClassRepository = Depends(get_class_repository),
    room_repository: RoomRepository = Depends(get_room_repository),
    requirement_repository: LessonRequirementRepository = Depends(
        get_lesson_requirement_repository
    ),
    availability_repository: AvailabilityRepository = Depends(get_availability_repository),
    school_day_repository: SchoolDayRepository = Depends(get_school_day_repository),
    time_period_repository: TimePeriodRepository = Depends(get_time_period_repository),
    scheduling_config_repository: SchedulingConfigRepository = Depends(
        get_scheduling_config_repository
    ),
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> RescheduleUseCase:
    return RescheduleUseCase(
        schedule_repository=schedule_repository,
        schedule_version_repository=schedule_version_repository,
        rescheduling_event_repository=rescheduling_event_repository,
        teacher_repository=teacher_repository,
        class_repository=class_repository,
        room_repository=room_repository,
        requirement_repository=requirement_repository,
        availability_repository=availability_repository,
        school_day_repository=school_day_repository,
        time_period_repository=time_period_repository,
        scheduling_config_repository=scheduling_config_repository,
        audit_repository=audit_repository,
    )
