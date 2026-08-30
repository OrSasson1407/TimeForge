/** Mirrors backend/app/api/schemas/catalog.py — the seven school-scoped
 * catalog entities sharing the generic list/get/upsert shape. */
import type { RoomStatus, TimePeriodKind, Weekday } from './enums'

export interface Teacher {
  id: string
  school_id: string
  name: string
  email: string
  subject_ids: string[]
  max_weekly_load: number
  max_consecutive: number
}

export interface TeacherUpsertRequest {
  name: string
  email: string
  subject_ids: string[]
  max_weekly_load: number
  max_consecutive: number
}

export interface Class {
  id: string
  school_id: string
  name: string
  grade: number
  student_count: number
  home_room_id: string | null
}

export interface ClassUpsertRequest {
  name: string
  grade: number
  student_count: number
  home_room_id: string | null
}

export interface Subject {
  id: string
  school_id: string
  name: string
  code: string
  required_capability: string | null
  max_daily_occurrences: number
  min_spacing_days: number
}

export interface SubjectUpsertRequest {
  name: string
  code: string
  required_capability: string | null
  max_daily_occurrences: number
  min_spacing_days: number
}

export interface Room {
  id: string
  school_id: string
  name: string
  capacity: number
  room_type: string
  capabilities: string[]
  status: RoomStatus
}

export interface RoomUpsertRequest {
  name: string
  capacity: number
  room_type: string
  capabilities: string[]
  status: RoomStatus
}

export interface SchoolDay {
  id: string
  school_id: string
  weekday: Weekday
  is_active: boolean
}

export interface SchoolDayUpsertRequest {
  weekday: Weekday
  is_active: boolean
}

export interface TimePeriod {
  id: string
  school_id: string
  index: number
  start_time: string
  end_time: string
  kind: TimePeriodKind
}

export interface TimePeriodUpsertRequest {
  index: number
  start_time: string
  end_time: string
  kind: TimePeriodKind
}

export interface LessonRequirement {
  id: string
  school_id: string
  class_id: string
  subject_id: string
  weekly_periods: number
  required_capability: string | null
}

export interface LessonRequirementUpsertRequest {
  class_id: string
  subject_id: string
  weekly_periods: number
  required_capability: string | null
}
