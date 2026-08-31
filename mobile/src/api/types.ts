/** Mirrors the backend's `MyTimetableResponse`
 * (backend/app/api/schemas/schedule.py). Deliberately name-bearing rather
 * than id-bearing: the phone must be able to render a cached timetable with
 * no further requests. */

export type Weekday =
  | 'MONDAY'
  | 'TUESDAY'
  | 'WEDNESDAY'
  | 'THURSDAY'
  | 'FRIDAY'
  | 'SATURDAY'
  | 'SUNDAY'

export interface TimetableEntry {
  assignment_id: string
  day_id: string
  weekday: Weekday
  time_period_id: string
  period_index: number
  /** "HH:MM:SS" */
  start_time: string
  end_time: string
  class_name: string
  room_name: string
  subject_code: string
  subject_name: string
}

export interface MyTimetable {
  /** null when nothing has been published for this school yet — a normal
   * empty state, not an error. */
  version_id: string | null
  entries: TimetableEntry[]
}

/** Mirrors the backend's `UserResponse`. The mobile app needs `school_id`
 * (to scope every request) and `teacher_id` (an account without one has no
 * timetable to show). */
export interface CurrentUser {
  id: string
  role: 'ADMIN' | 'TEACHER' | 'PENDING'
  school_id: string
  display_name: string
  teacher_id: string | null
  email_verified: boolean
  is_active: boolean
  created_at: string
}
