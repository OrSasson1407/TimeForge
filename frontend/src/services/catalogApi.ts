import { createCrudApi } from './crudApi'
import type {
  Class,
  ClassUpsertRequest,
  LessonRequirement,
  LessonRequirementUpsertRequest,
  Room,
  RoomUpsertRequest,
  SchoolDay,
  SchoolDayUpsertRequest,
  Subject,
  SubjectUpsertRequest,
  Teacher,
  TeacherUpsertRequest,
  TimePeriod,
  TimePeriodUpsertRequest,
} from '../types/catalog'

export const teacherApi = createCrudApi<Teacher, TeacherUpsertRequest>('/teachers')
export const classApi = createCrudApi<Class, ClassUpsertRequest>('/classes')
export const subjectApi = createCrudApi<Subject, SubjectUpsertRequest>('/subjects')
export const roomApi = createCrudApi<Room, RoomUpsertRequest>('/rooms')
export const schoolDayApi = createCrudApi<SchoolDay, SchoolDayUpsertRequest>('/school-days')
export const timePeriodApi = createCrudApi<TimePeriod, TimePeriodUpsertRequest>('/periods')
export const lessonRequirementApi = createCrudApi<
  LessonRequirement,
  LessonRequirementUpsertRequest
>('/lesson-requirements')
