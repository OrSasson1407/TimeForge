import { apiClient } from './apiClient'
import type { SchedulingConfig, SchedulingConfigUpdateRequest } from '../types/schedulingConfig'

export const schedulingConfigApi = {
  get: (schoolId: string) => apiClient.get<SchedulingConfig>(`/constraints?school_id=${schoolId}`),
  update: (schoolId: string, body: SchedulingConfigUpdateRequest) =>
    apiClient.put<SchedulingConfig>(`/constraints?school_id=${schoolId}`, body),
}
