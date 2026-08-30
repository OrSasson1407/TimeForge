/**
 * Mirrors backend/app/domain/models/enums.py. String literal unions, not TS
 * `enum` (tsconfig has `erasableSyntaxOnly` — a real `enum` compiles to
 * runtime code, which that option forbids); the values are exactly the
 * StrEnum string values the backend serializes, so no mapping is needed.
 */

export type Weekday =
  'MONDAY' | 'TUESDAY' | 'WEDNESDAY' | 'THURSDAY' | 'FRIDAY' | 'SATURDAY' | 'SUNDAY'

export const WEEKDAYS: Weekday[] = [
  'MONDAY',
  'TUESDAY',
  'WEDNESDAY',
  'THURSDAY',
  'FRIDAY',
  'SATURDAY',
  'SUNDAY',
]

export type TimePeriodKind = 'LESSON' | 'BREAK'

export type RoomStatus = 'ACTIVE' | 'CLOSED'

export type OwnerType = 'TEACHER' | 'CLASS'

export type ScheduleVersionStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'

export type UserRole = 'ADMIN' | 'TEACHER' | 'PENDING'

export type AuditOperation =
  | 'SCHEDULE_GENERATED'
  | 'SCHEDULE_PUBLISHED'
  | 'ASSIGNMENT_MOVED'
  | 'RESCHEDULED'
  | 'AVAILABILITY_CHANGED'
  | 'ROOM_STATUS_CHANGED'
  | 'CONSTRAINT_CONFIG_CHANGED'
  | 'ENTITY_CONFIGURED'
  | 'USER_REGISTERED'
  | 'USER_EMAIL_VERIFIED'
  | 'USER_APPROVED'
  | 'USER_REJECTED'
  | 'USER_SUSPENDED'
  | 'USER_REACTIVATED'

export type AuditEntityType =
  | 'SCHOOL'
  | 'TEACHER'
  | 'CLASS'
  | 'SUBJECT'
  | 'ROOM'
  | 'LESSON_REQUIREMENT'
  | 'AVAILABILITY'
  | 'SCHEDULE'
  | 'SCHEDULE_VERSION'
  | 'SCHEDULE_ASSIGNMENT'
  | 'SCHEDULING_CONFIG'
  | 'USER'

export type SolverStatus = 'VALID' | 'INFEASIBLE' | 'FAILED' | 'TIMEOUT'

export type MoveValidationResult = 'VALID' | 'WARNING' | 'INVALID'

export type Severity = 'ERROR' | 'WARNING'
