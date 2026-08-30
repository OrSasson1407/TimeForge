import { apiClient } from './apiClient'
import type { School, SchoolUpsertRequest } from '../types/school'

export const schoolApi = {
  get: (schoolId: string) => apiClient.get<School>(`/schools/${schoolId}`),
  upsert: (schoolId: string, body: SchoolUpsertRequest) =>
    apiClient.put<School>(`/schools/${schoolId}`, body),
}
