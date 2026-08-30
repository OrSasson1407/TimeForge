import type { OwnerType } from './enums'

/** Mirrors backend/app/api/schemas/availability.py. */
export interface Availability {
  id: string
  school_id: string
  owner_type: OwnerType
  owner_id: string
  day_id: string | null
  time_period_id: string
  is_available: boolean
  preference_weight: number
}

export interface AvailabilityUpsertRequest {
  owner_type: OwnerType
  owner_id: string
  day_id: string | null
  time_period_id: string
  is_available: boolean
  preference_weight: number
}
