"""Shared FastAPI TestClient fixture (docs/07-CODE_STANDARDS.md #23): every
API test overrides `app.dependency_overrides` with the in-memory fakes from
`tests.support.fakes`, never a live Firestore emulator (the Phase 6 scope
decision documented in `tests/infrastructure/firebase`'s module docstring).
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_audit_repository,
    get_availability_repository,
    get_class_repository,
    get_current_user,
    get_email_sender,
    get_identity_admin,
    get_lesson_requirement_repository,
    get_register_rate_limiter,
    get_rescheduling_event_repository,
    get_resend_code_rate_limiter,
    get_room_repository,
    get_schedule_repository,
    get_schedule_version_repository,
    get_scheduling_config_repository,
    get_school_day_repository,
    get_school_repository,
    get_settings,
    get_subject_repository,
    get_teacher_repository,
    get_time_period_repository,
    get_user_repository,
    get_verification_repository,
)
from app.core.config import Settings
from app.core.rate_limit import RateLimiter
from app.domain.models import User, UserRole
from app.main import app
from tests.support.fakes import (
    FakeAuditRepository,
    FakeAvailabilityRepository,
    FakeEmailSender,
    FakeIdentityAdmin,
    FakeRepository,
    FakeReschedulingEventRepository,
    FakeScheduleRepository,
    FakeScheduleVersionRepository,
    FakeSchedulingConfigRepository,
    FakeSchoolRepository,
    FakeUserRepository,
    FakeVerificationCodeRepository,
)


@dataclass(frozen=True, slots=True)
class ApiFixtures:
    client: TestClient
    schools: FakeSchoolRepository
    teachers: Any  # FakeRepository[Teacher]
    classes: Any  # FakeRepository[Class]
    subjects: Any  # FakeRepository[Subject]
    rooms: Any  # FakeRepository[Room]
    school_days: Any  # FakeRepository[SchoolDay]
    time_periods: Any  # FakeRepository[TimePeriod]
    lesson_requirements: Any  # FakeRepository[LessonRequirement]
    availability: FakeAvailabilityRepository
    scheduling_config: FakeSchedulingConfigRepository
    schedules: FakeScheduleRepository
    schedule_versions: FakeScheduleVersionRepository
    rescheduling_events: FakeReschedulingEventRepository
    audit: FakeAuditRepository
    users: FakeUserRepository
    verifications: FakeVerificationCodeRepository
    identity_admin: FakeIdentityAdmin
    email_sender: FakeEmailSender

    def set_current_user(self, user: User) -> None:
        app.dependency_overrides[get_current_user] = lambda: user
        self.users.save(user)

    def admin(self, *, school_id: str = "s1", user_id: str = "admin_1") -> User:
        user = User(id=user_id, role=UserRole.ADMIN, school_id=school_id, display_name="Dana Admin")
        self.set_current_user(user)
        return user

    def teacher(
        self, *, school_id: str = "s1", user_id: str = "teacher_user_1", teacher_id: str = "t1"
    ) -> User:
        user = User(
            id=user_id,
            role=UserRole.TEACHER,
            school_id=school_id,
            display_name="Tal Teacher",
            teacher_id=teacher_id,
        )
        self.set_current_user(user)
        return user


@pytest.fixture
def api() -> Iterator[ApiFixtures]:
    schools = FakeSchoolRepository()
    teachers = FakeRepository()
    classes = FakeRepository()
    subjects = FakeRepository()
    rooms = FakeRepository()
    school_days = FakeRepository()
    time_periods = FakeRepository()
    lesson_requirements = FakeRepository()
    availability = FakeAvailabilityRepository()
    scheduling_config = FakeSchedulingConfigRepository()
    schedules = FakeScheduleRepository()
    schedule_versions = FakeScheduleVersionRepository(schedules)
    rescheduling_events = FakeReschedulingEventRepository()
    audit = FakeAuditRepository()
    users = FakeUserRepository()
    verifications = FakeVerificationCodeRepository()
    identity_admin = FakeIdentityAdmin()
    email_sender = FakeEmailSender()
    # Generous, per-test-fresh limiters: tests exercising throttling itself
    # override these again with a tight limiter (see test_registration.py).
    register_rate_limiter = RateLimiter(max_calls=1000, window_seconds=3600)
    resend_rate_limiter = RateLimiter(max_calls=1000, window_seconds=900)
    # password_check_breached defaults to True (real behavior); tests force
    # it off so the suite never makes a live network call to HaveIBeenPwned.
    # recaptcha_secret_key is forced to None too — Settings() still loads
    # backend/.env (env_file isn't disabled here), so without this override
    # a real RECAPTCHA_SECRET_KEY in that file would make verify_recaptcha
    # attempt a real network call against the tests' fake token and reject
    # every registration in the suite (see app/core/security.py).
    test_settings = Settings(password_check_breached=False, recaptcha_secret_key=None)

    app.dependency_overrides[get_school_repository] = lambda: schools
    app.dependency_overrides[get_teacher_repository] = lambda: teachers
    app.dependency_overrides[get_class_repository] = lambda: classes
    app.dependency_overrides[get_subject_repository] = lambda: subjects
    app.dependency_overrides[get_room_repository] = lambda: rooms
    app.dependency_overrides[get_school_day_repository] = lambda: school_days
    app.dependency_overrides[get_time_period_repository] = lambda: time_periods
    app.dependency_overrides[get_lesson_requirement_repository] = lambda: lesson_requirements
    app.dependency_overrides[get_availability_repository] = lambda: availability
    app.dependency_overrides[get_scheduling_config_repository] = lambda: scheduling_config
    app.dependency_overrides[get_schedule_repository] = lambda: schedules
    app.dependency_overrides[get_schedule_version_repository] = lambda: schedule_versions
    app.dependency_overrides[get_rescheduling_event_repository] = lambda: rescheduling_events
    app.dependency_overrides[get_audit_repository] = lambda: audit
    app.dependency_overrides[get_user_repository] = lambda: users
    app.dependency_overrides[get_verification_repository] = lambda: verifications
    app.dependency_overrides[get_identity_admin] = lambda: identity_admin
    app.dependency_overrides[get_email_sender] = lambda: email_sender
    app.dependency_overrides[get_register_rate_limiter] = lambda: register_rate_limiter
    app.dependency_overrides[get_resend_code_rate_limiter] = lambda: resend_rate_limiter
    app.dependency_overrides[get_settings] = lambda: test_settings

    try:
        yield ApiFixtures(
            client=TestClient(app),
            schools=schools,
            teachers=teachers,
            classes=classes,
            subjects=subjects,
            rooms=rooms,
            school_days=school_days,
            time_periods=time_periods,
            lesson_requirements=lesson_requirements,
            availability=availability,
            scheduling_config=scheduling_config,
            schedules=schedules,
            schedule_versions=schedule_versions,
            rescheduling_events=rescheduling_events,
            audit=audit,
            users=users,
            verifications=verifications,
            identity_admin=identity_admin,
            email_sender=email_sender,
        )
    finally:
        app.dependency_overrides.clear()
