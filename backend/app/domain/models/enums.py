"""Shared vocabulary enums for the domain model (docs/04-DESIGN.md #1-2).

StrEnum is used throughout so values serialize as plain strings (matching
the Firestore document shapes in docs/05-DATABASE.md) without a separate
mapping step. Values are explicit (not auto()) to match the exact
UPPER_SNAKE_CASE strings used in docs/05-DATABASE.md's document examples.
"""

from enum import StrEnum


class Weekday(StrEnum):
    """A calendar weekday. SchoolDay.is_active selects which are in use,
    so a school's week is never hardcoded to Monday-Friday (master prompt #14)."""

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class TimePeriodKind(StrEnum):
    """Whether a TimePeriod may host a lesson or is a mandatory break (HC-007)."""

    LESSON = "LESSON"
    BREAK = "BREAK"


class RoomStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class OwnerType(StrEnum):
    """Who an Availability record belongs to."""

    TEACHER = "TEACHER"
    CLASS = "CLASS"


class ScheduleVersionStatus(StrEnum):
    """docs/04-DESIGN.md #25 state machine."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class ReschedulingEventType(StrEnum):
    """docs/03-ARCHITECTURE.md Edge Case Analysis #10-13."""

    TEACHER_UNAVAILABLE = "TEACHER_UNAVAILABLE"
    ROOM_UNAVAILABLE = "ROOM_UNAVAILABLE"
    REQUIREMENT_ADDED = "REQUIREMENT_ADDED"
    REQUIREMENT_REMOVED = "REQUIREMENT_REMOVED"
    TEACHER_REPLACED = "TEACHER_REPLACED"


class UserRole(StrEnum):
    """docs/02-PRD.md #27. PENDING is a self-registered account that has
    verified its email/phone but has no permissions yet — an Admin must
    approve it (assigning ADMIN or TEACHER, and a teacher_id for the
    latter) before it can do anything but read its own /auth/me record
    (docs/02-PRD.md #28a, added in the registration feature)."""

    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    PENDING = "PENDING"


class AuditOperation(StrEnum):
    """docs/04-DESIGN.md #22; master prompt Audit Log examples."""

    SCHEDULE_GENERATED = "SCHEDULE_GENERATED"
    SCHEDULE_PUBLISHED = "SCHEDULE_PUBLISHED"
    ASSIGNMENT_MOVED = "ASSIGNMENT_MOVED"
    RESCHEDULED = "RESCHEDULED"
    AVAILABILITY_CHANGED = "AVAILABILITY_CHANGED"
    ROOM_STATUS_CHANGED = "ROOM_STATUS_CHANGED"
    CONSTRAINT_CONFIG_CHANGED = "CONSTRAINT_CONFIG_CHANGED"
    ENTITY_CONFIGURED = "ENTITY_CONFIGURED"
    USER_REGISTERED = "USER_REGISTERED"
    USER_EMAIL_VERIFIED = "USER_EMAIL_VERIFIED"
    USER_APPROVED = "USER_APPROVED"
    USER_REJECTED = "USER_REJECTED"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_REACTIVATED = "USER_REACTIVATED"


class AuditEntityType(StrEnum):
    SCHOOL = "SCHOOL"
    TEACHER = "TEACHER"
    CLASS = "CLASS"
    SUBJECT = "SUBJECT"
    ROOM = "ROOM"
    LESSON_REQUIREMENT = "LESSON_REQUIREMENT"
    AVAILABILITY = "AVAILABILITY"
    SCHEDULE = "SCHEDULE"
    SCHEDULE_VERSION = "SCHEDULE_VERSION"
    SCHEDULE_ASSIGNMENT = "SCHEDULE_ASSIGNMENT"
    SCHEDULING_CONFIG = "SCHEDULING_CONFIG"
    USER = "USER"
