import { apiClient } from './apiClient'
import type {
  ReportDisruptionRequest,
  RescheduleResponse,
  ReschedulingEvent,
} from '../types/rescheduling'

export const reschedulingApi = {
  reschedule: (schoolId: string, body: ReportDisruptionRequest) =>
    apiClient.post<RescheduleResponse>(`/schedules/reschedule?school_id=${schoolId}`, body),
  listEvents: (schoolId: string) =>
    apiClient.get<ReschedulingEvent[]>(`/schedules/rescheduling-events?school_id=${schoolId}`),
}
