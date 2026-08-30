/** Mirrors backend/app/api/schemas/school.py. */
export interface School {
  id: string
  name: string
  timezone: string
}

export interface SchoolUpsertRequest {
  name: string
  timezone: string
}
