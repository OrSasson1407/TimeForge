import { createCrudHooks } from './useCrud'
import {
  classApi,
  lessonRequirementApi,
  roomApi,
  schoolDayApi,
  subjectApi,
  teacherApi,
  timePeriodApi,
} from '../services/catalogApi'

export const teacherHooks = createCrudHooks('teachers', teacherApi)
export const classHooks = createCrudHooks('classes', classApi)
export const subjectHooks = createCrudHooks('subjects', subjectApi)
export const roomHooks = createCrudHooks('rooms', roomApi)
export const schoolDayHooks = createCrudHooks('school-days', schoolDayApi)
export const timePeriodHooks = createCrudHooks('periods', timePeriodApi)
export const lessonRequirementHooks = createCrudHooks('lesson-requirements', lessonRequirementApi)
