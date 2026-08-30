import type { EntityManagerConfig } from './EntityManager'
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
} from '../../types/catalog'
import { WEEKDAYS } from '../../types/enums'

function splitList(value: string): string[] {
  return value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
}

export const teacherConfig: EntityManagerConfig<Teacher, TeacherUpsertRequest> = {
  titleKey: 'catalog.teachers.title',
  fields: [
    { key: 'name', labelKey: 'catalog.teachers.name', input: 'text' },
    { key: 'email', labelKey: 'catalog.teachers.email', input: 'text' },
    {
      key: 'subject_ids',
      labelKey: 'catalog.teachers.subjectIds',
      input: 'text',
      helpTextKey: 'catalog.teachers.subjectIdsHelp',
    },
    { key: 'max_weekly_load', labelKey: 'catalog.teachers.maxWeeklyLoad', input: 'number' },
    { key: 'max_consecutive', labelKey: 'catalog.teachers.maxConsecutive', input: 'number' },
  ],
  columns: [
    { key: 'id', labelKey: 'entityManager.id', render: (t) => t.id },
    { key: 'name', labelKey: 'catalog.teachers.name', render: (t) => t.name },
    { key: 'email', labelKey: 'catalog.teachers.email', render: (t) => t.email },
    {
      key: 'subjects',
      labelKey: 'catalog.teachers.columnSubjects',
      render: (t) => t.subject_ids.join(', '),
    },
  ],
  toFormState: (t) => ({
    name: t.name,
    email: t.email,
    subject_ids: t.subject_ids.join(', '),
    max_weekly_load: String(t.max_weekly_load),
    max_consecutive: String(t.max_consecutive),
  }),
  emptyFormState: {
    name: '',
    email: '',
    subject_ids: '',
    max_weekly_load: '30',
    max_consecutive: '4',
  },
  toUpsert: (form) => ({
    name: form.name,
    email: form.email,
    subject_ids: splitList(form.subject_ids),
    max_weekly_load: Number(form.max_weekly_load) || 30,
    max_consecutive: Number(form.max_consecutive) || 4,
  }),
}

export const classConfig: EntityManagerConfig<Class, ClassUpsertRequest> = {
  titleKey: 'catalog.classes.title',
  fields: [
    { key: 'name', labelKey: 'catalog.classes.name', input: 'text' },
    { key: 'grade', labelKey: 'catalog.classes.grade', input: 'number' },
    { key: 'student_count', labelKey: 'catalog.classes.studentCount', input: 'number' },
    { key: 'home_room_id', labelKey: 'catalog.classes.homeRoomId', input: 'text' },
  ],
  columns: [
    { key: 'id', labelKey: 'entityManager.id', render: (c) => c.id },
    { key: 'name', labelKey: 'catalog.classes.name', render: (c) => c.name },
    { key: 'grade', labelKey: 'catalog.classes.grade', render: (c) => String(c.grade) },
    {
      key: 'student_count',
      labelKey: 'catalog.classes.columnStudents',
      render: (c) => String(c.student_count),
    },
  ],
  toFormState: (c) => ({
    name: c.name,
    grade: String(c.grade),
    student_count: String(c.student_count),
    home_room_id: c.home_room_id ?? '',
  }),
  emptyFormState: { name: '', grade: '0', student_count: '25', home_room_id: '' },
  toUpsert: (form) => ({
    name: form.name,
    grade: Number(form.grade) || 0,
    student_count: Number(form.student_count) || 1,
    home_room_id: form.home_room_id || null,
  }),
}

export const subjectConfig: EntityManagerConfig<Subject, SubjectUpsertRequest> = {
  titleKey: 'catalog.subjects.title',
  fields: [
    { key: 'name', labelKey: 'catalog.subjects.name', input: 'text' },
    { key: 'code', labelKey: 'catalog.subjects.code', input: 'text' },
    {
      key: 'required_capability',
      labelKey: 'catalog.subjects.requiredCapability',
      input: 'text',
    },
    {
      key: 'max_daily_occurrences',
      labelKey: 'catalog.subjects.maxDailyOccurrences',
      input: 'number',
    },
    { key: 'min_spacing_days', labelKey: 'catalog.subjects.minSpacingDays', input: 'number' },
  ],
  columns: [
    { key: 'id', labelKey: 'entityManager.id', render: (s) => s.id },
    { key: 'name', labelKey: 'catalog.subjects.name', render: (s) => s.name },
    { key: 'code', labelKey: 'catalog.subjects.code', render: (s) => s.code },
    {
      key: 'capability',
      labelKey: 'catalog.subjects.columnCapability',
      render: (s) => s.required_capability ?? '—',
    },
  ],
  toFormState: (s) => ({
    name: s.name,
    code: s.code,
    required_capability: s.required_capability ?? '',
    max_daily_occurrences: String(s.max_daily_occurrences),
    min_spacing_days: String(s.min_spacing_days),
  }),
  emptyFormState: {
    name: '',
    code: '',
    required_capability: '',
    max_daily_occurrences: '1',
    min_spacing_days: '0',
  },
  toUpsert: (form) => ({
    name: form.name,
    code: form.code,
    required_capability: form.required_capability || null,
    max_daily_occurrences: Number(form.max_daily_occurrences) || 1,
    min_spacing_days: Number(form.min_spacing_days) || 0,
  }),
}

export const roomConfig: EntityManagerConfig<Room, RoomUpsertRequest> = {
  titleKey: 'catalog.rooms.title',
  fields: [
    { key: 'name', labelKey: 'catalog.rooms.name', input: 'text' },
    { key: 'capacity', labelKey: 'catalog.rooms.capacity', input: 'number' },
    {
      key: 'room_type',
      labelKey: 'catalog.rooms.roomType',
      input: 'text',
      helpTextKey: 'catalog.rooms.roomTypeHelp',
    },
    { key: 'capabilities', labelKey: 'catalog.rooms.capabilities', input: 'text' },
    {
      key: 'status',
      labelKey: 'catalog.rooms.status',
      input: 'select',
      options: ['ACTIVE', 'CLOSED'],
    },
  ],
  columns: [
    { key: 'id', labelKey: 'entityManager.id', render: (r) => r.id },
    { key: 'name', labelKey: 'catalog.rooms.name', render: (r) => r.name },
    { key: 'capacity', labelKey: 'catalog.rooms.capacity', render: (r) => String(r.capacity) },
    { key: 'status', labelKey: 'catalog.rooms.status', render: (r) => r.status },
  ],
  toFormState: (r) => ({
    name: r.name,
    capacity: String(r.capacity),
    room_type: r.room_type,
    capabilities: r.capabilities.join(', '),
    status: r.status,
  }),
  emptyFormState: {
    name: '',
    capacity: '30',
    room_type: 'STANDARD',
    capabilities: '',
    status: 'ACTIVE',
  },
  toUpsert: (form) => ({
    name: form.name,
    capacity: Number(form.capacity) || 1,
    room_type: form.room_type,
    capabilities: splitList(form.capabilities),
    status: form.status === 'CLOSED' ? 'CLOSED' : 'ACTIVE',
  }),
}

export const schoolDayConfig: EntityManagerConfig<SchoolDay, SchoolDayUpsertRequest> = {
  titleKey: 'catalog.schoolDays.title',
  fields: [
    { key: 'weekday', labelKey: 'catalog.schoolDays.weekday', input: 'select', options: WEEKDAYS },
    { key: 'is_active', labelKey: 'catalog.schoolDays.isActive', input: 'checkbox' },
  ],
  columns: [
    { key: 'id', labelKey: 'entityManager.id', render: (d) => d.id },
    { key: 'weekday', labelKey: 'catalog.schoolDays.weekday', render: (d) => d.weekday },
    {
      key: 'is_active',
      labelKey: 'catalog.schoolDays.isActive',
      render: (d) => (d.is_active ? 'Yes' : 'No'),
    },
  ],
  toFormState: (d) => ({ weekday: d.weekday, is_active: d.is_active ? 'true' : 'false' }),
  emptyFormState: { weekday: 'MONDAY', is_active: 'true' },
  toUpsert: (form) => ({
    weekday: (form.weekday || 'MONDAY') as SchoolDayUpsertRequest['weekday'],
    is_active: form.is_active === 'true',
  }),
}

export const timePeriodConfig: EntityManagerConfig<TimePeriod, TimePeriodUpsertRequest> = {
  titleKey: 'catalog.timePeriods.title',
  fields: [
    { key: 'index', labelKey: 'catalog.timePeriods.index', input: 'number' },
    { key: 'start_time', labelKey: 'catalog.timePeriods.startTime', input: 'text' },
    { key: 'end_time', labelKey: 'catalog.timePeriods.endTime', input: 'text' },
    {
      key: 'kind',
      labelKey: 'catalog.timePeriods.kind',
      input: 'select',
      options: ['LESSON', 'BREAK'],
    },
  ],
  columns: [
    { key: 'id', labelKey: 'entityManager.id', render: (p) => p.id },
    { key: 'index', labelKey: 'catalog.timePeriods.columnOrder', render: (p) => String(p.index) },
    {
      key: 'time',
      labelKey: 'catalog.timePeriods.columnTime',
      render: (p) => `${p.start_time}–${p.end_time}`,
    },
    { key: 'kind', labelKey: 'catalog.timePeriods.kind', render: (p) => p.kind },
  ],
  toFormState: (p) => ({
    index: String(p.index),
    start_time: p.start_time,
    end_time: p.end_time,
    kind: p.kind,
  }),
  emptyFormState: { index: '0', start_time: '08:00:00', end_time: '08:45:00', kind: 'LESSON' },
  toUpsert: (form) => ({
    index: Number(form.index) || 0,
    start_time: form.start_time,
    end_time: form.end_time,
    kind: form.kind === 'BREAK' ? 'BREAK' : 'LESSON',
  }),
}

export const lessonRequirementConfig: EntityManagerConfig<
  LessonRequirement,
  LessonRequirementUpsertRequest
> = {
  titleKey: 'catalog.lessonRequirements.title',
  fields: [
    { key: 'class_id', labelKey: 'catalog.lessonRequirements.classId', input: 'text' },
    { key: 'subject_id', labelKey: 'catalog.lessonRequirements.subjectId', input: 'text' },
    {
      key: 'weekly_periods',
      labelKey: 'catalog.lessonRequirements.weeklyPeriods',
      input: 'number',
    },
    {
      key: 'required_capability',
      labelKey: 'catalog.lessonRequirements.requiredCapability',
      input: 'text',
    },
  ],
  columns: [
    { key: 'id', labelKey: 'entityManager.id', render: (r) => r.id },
    {
      key: 'class_id',
      labelKey: 'catalog.lessonRequirements.columnClass',
      render: (r) => r.class_id,
    },
    {
      key: 'subject_id',
      labelKey: 'catalog.lessonRequirements.columnSubject',
      render: (r) => r.subject_id,
    },
    {
      key: 'weekly_periods',
      labelKey: 'catalog.lessonRequirements.weeklyPeriods',
      render: (r) => String(r.weekly_periods),
    },
  ],
  toFormState: (r) => ({
    class_id: r.class_id,
    subject_id: r.subject_id,
    weekly_periods: String(r.weekly_periods),
    required_capability: r.required_capability ?? '',
  }),
  emptyFormState: { class_id: '', subject_id: '', weekly_periods: '1', required_capability: '' },
  toUpsert: (form) => ({
    class_id: form.class_id,
    subject_id: form.subject_id,
    weekly_periods: Number(form.weekly_periods) || 1,
    required_capability: form.required_capability || null,
  }),
}
