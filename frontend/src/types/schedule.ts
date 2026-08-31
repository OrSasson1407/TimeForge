/** Mirrors backend/app/api/schemas/schedule.py — the scheduling-workflow
 * request/response shapes. */
import type { ScheduleVersionStatus, Severity, SolverStatus } from './enums'

export interface Schedule {
  id: string
  school_id: string
  active_version_id: string | null
}

export interface ScheduleScore {
  hard_violations: number
  soft_penalty: number
  quality: number
}

export interface ScheduleVersion {
  id: string
  schedule_id: string
  status: ScheduleVersionStatus
  created_by: string
  created_at: string
  parent_version_id: string | null
  score: ScheduleScore | null
  reason: string | null
  assignment_count: number
  version_tag: number
}

export interface ScheduleAssignment {
  id: string
  version_id: string
  lesson_id: string
  teacher_id: string
  class_id: string
  room_id: string
  time_period_id: string
  day_id: string
}

export interface GenerateScheduleRequest {
  request_id: string
  reason?: string | null
}

export interface BottleneckReport {
  subject_id: string
  required_capability: string | null
  required: number
  available: number
  shortage: number
  affected_class_ids: string[]
  affected_teacher_ids: string[]
}

export interface InfeasibilityReport {
  bottlenecks: BottleneckReport[]
  note: string | null
}

export interface SearchStats {
  candidates_tried: number
  backtracks: number
  /** Decision frames skipped by conflict-directed backjumping — see the
   * backend's `scheduling/conflicts.py`. */
  backjumps: number
  duration_seconds: number
}

export interface GenerateScheduleResponse {
  status: SolverStatus
  version: ScheduleVersion | null
  infeasibility: InfeasibilityReport | null
  error: string | null
  stats: SearchStats
}

export interface ProposedMove {
  assignment_id: string
  teacher_id: string
  room_id: string
  day_id: string
  time_period_id: string
}

export interface Violation {
  constraint_id: string
  severity: Severity
  message: string
  involved_entities: string[]
}

export interface ValidateMoveResponse {
  result: 'VALID' | 'WARNING' | 'INVALID'
  message: string | null
  violation: Violation | null
}

export interface ApplyMoveRequest extends ProposedMove {
  expected_version_tag: number
}

export interface PublishRequest {
  expected_version_tag: number
}

export interface TeacherWorkload {
  teacher_id: string
  teacher_name: string
  assigned_periods: number
  max_weekly_load: number
  /** assigned_periods / max_weekly_load, 0 when the max is unset. */
  load_ratio: number
}

export interface RoomUtilization {
  room_id: string
  room_name: string
  used_slots: number
  /** 0 for a CLOSED room — it offers no slots at all, which is different
   * from an open room nobody booked. */
  available_slots: number
  utilization_ratio: number
}

export interface ClassCoverage {
  class_id: string
  class_name: string
  scheduled_periods: number
  required_periods: number
  is_complete: boolean
}

export interface ScheduleAnalytics {
  total_assignments: number
  lesson_slots_per_week: number
  /** Population standard deviation of periods across teachers — 0 is a
   * perfectly even split. */
  workload_spread: number
  teacher_workloads: TeacherWorkload[]
  room_utilizations: RoomUtilization[]
  class_coverages: ClassCoverage[]
}

export interface AssignmentDiffEntry {
  lesson_id: string
  before: ScheduleAssignment | null
  after: ScheduleAssignment | null
}

export interface CompareVersionsResponse {
  from_version_id: string
  to_version_id: string
  added: AssignmentDiffEntry[]
  removed: AssignmentDiffEntry[]
  moved: AssignmentDiffEntry[]
  unchanged_count: number
}
