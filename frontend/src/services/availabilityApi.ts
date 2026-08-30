import { apiClient } from './apiClient'
import type { OwnerType } from '../types/enums'
import type { Availability, AvailabilityUpsertRequest } from '../types/availability'

export const availabilityApi = {
  listAll: (schoolId: string) =>
    apiClient.get<Availability[]>(`/availability?school_id=${schoolId}`),
  listForOwner: (schoolId: string, ownerType: OwnerType, ownerId: string) =>
    apiClient.get<Availability[]>(
      `/availability?school_id=${schoolId}&owner_type=${ownerType}&owner_id=${ownerId}`,
    ),
  upsert: (schoolId: string, id: string, body: AvailabilityUpsertRequest) =>
    apiClient.put<Availability>(`/availability/${id}?school_id=${schoolId}`, body),
}
