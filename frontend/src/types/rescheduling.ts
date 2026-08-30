/** Mirrors backend/app/api/schemas/rescheduling.py. */
import type { ScheduleVersion, InfeasibilityReport } from './schedule'

export type ReschedulingEventType =
  | 'TEACHER_UNAVAILABLE'
  | 'ROOM_UNAVAILABLE'
  | 'REQUIREMENT_ADDED'
  | 'REQUIREMENT_REMOVED'
  | 'TEACHER_REPLACED'

export type ReschedulingStatus = 'REPAIRED' | 'UNREPAIRABLE' | 'FAILED'

export interface TimeSlotInput {
  day_id: string
  time_period_id: string
}

export interface ReportDisruptionRequest {
  request_id: string
  event_type: ReschedulingEventType
  target_entity_id: string
  affected_slots: TimeSlotInput[]
  reason: string
}

export interface ReschedulingEvent {
  id: string
  schedule_id: string
  type: ReschedulingEventType
  target_entity_id: string
  affected_slots: TimeSlotInput[]
  reason: string
  reported_at: string
}

export interface DisruptionCost {
  moved_assignments: number
  changed_rooms: number
  changed_teachers: number
  soft_constraint_penalty_delta: number
  total: number
}

export interface RescheduleResponse {
  status: ReschedulingStatus
  version: ScheduleVersion | null
  directly_affected_lesson_ids: string[]
  disruption_cost: DisruptionCost | null
  infeasibility: InfeasibilityReport | null
  error: string | null
}
