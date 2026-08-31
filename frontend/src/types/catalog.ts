/**
 * The seven school-scoped catalog entities.
 *
 * These are ALIASES over `api.generated.ts`, which is generated from the
 * backend's own OpenAPI schema — not hand-maintained copies of it. That is
 * the point: rename a field or change a type in
 * `backend/app/api/schemas/catalog.py`, regenerate, and every place in this
 * app that used the old shape stops compiling. Previously the two sides
 * were independent declarations that could silently drift until something
 * broke at runtime.
 *
 * The short names are kept (`Teacher`, not `TeacherResponse`) so call sites
 * read naturally and so this indirection can change without touching them.
 */
import type { components } from './api.generated'

type Schemas = components['schemas']

export type Teacher = Schemas['TeacherResponse']
export type TeacherUpsertRequest = Schemas['TeacherUpsertRequest']

export type Class = Schemas['ClassResponse']
export type ClassUpsertRequest = Schemas['ClassUpsertRequest']

export type Subject = Schemas['SubjectResponse']
export type SubjectUpsertRequest = Schemas['SubjectUpsertRequest']

export type Room = Schemas['RoomResponse']
export type RoomUpsertRequest = Schemas['RoomUpsertRequest']

export type SchoolDay = Schemas['SchoolDayResponse']
export type SchoolDayUpsertRequest = Schemas['SchoolDayUpsertRequest']

export type TimePeriod = Schemas['TimePeriodResponse']
export type TimePeriodUpsertRequest = Schemas['TimePeriodUpsertRequest']

export type LessonRequirement = Schemas['LessonRequirementResponse']
export type LessonRequirementUpsertRequest = Schemas['LessonRequirementUpsertRequest']
