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
  title: 'Teachers',
  fields: [
    { key: 'name', label: 'Name', input: 'text' },
    { key: 'email', label: 'Email', input: 'text' },
    {
      key: 'subject_ids',
      label: 'Subjects (comma-separated subject IDs)',
      input: 'text',
      helpText: 'e.g. MATH, SCI',
    },
    { key: 'max_weekly_load', label: 'Max weekly load', input: 'number' },
    { key: 'max_consecutive', label: 'Max consecutive lessons', input: 'number' },
  ],
  columns: [
    { key: 'id', label: 'ID', render: (t) => t.id },
    { key: 'name', label: 'Name', render: (t) => t.name },
    { key: 'email', label: 'Email', render: (t) => t.email },
    { key: 'subjects', label: 'Subjects', render: (t) => t.subject_ids.join(', ') },
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
  title: 'Classes',
  fields: [
    { key: 'name', label: 'Name', input: 'text' },
    { key: 'grade', label: 'Grade', input: 'number' },
    { key: 'student_count', label: 'Student count', input: 'number' },
    { key: 'home_room_id', label: 'Home room ID (optional)', input: 'text' },
  ],
  columns: [
    { key: 'id', label: 'ID', render: (c) => c.id },
    { key: 'name', label: 'Name', render: (c) => c.name },
    { key: 'grade', label: 'Grade', render: (c) => String(c.grade) },
    { key: 'student_count', label: 'Students', render: (c) => String(c.student_count) },
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
  title: 'Subjects',
  fields: [
    { key: 'name', label: 'Name', input: 'text' },
    { key: 'code', label: 'Code', input: 'text' },
    { key: 'required_capability', label: 'Required room capability (optional)', input: 'text' },
    { key: 'max_daily_occurrences', label: 'Max daily occurrences', input: 'number' },
    { key: 'min_spacing_days', label: 'Min spacing (days)', input: 'number' },
  ],
  columns: [
    { key: 'id', label: 'ID', render: (s) => s.id },
    { key: 'name', label: 'Name', render: (s) => s.name },
    { key: 'code', label: 'Code', render: (s) => s.code },
    {
      key: 'capability',
      label: 'Required capability',
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
  title: 'Rooms',
  fields: [
    { key: 'name', label: 'Name', input: 'text' },
    { key: 'capacity', label: 'Capacity', input: 'number' },
    { key: 'room_type', label: 'Room type', input: 'text', helpText: 'e.g. STANDARD, LAB' },
    { key: 'capabilities', label: 'Capabilities (comma-separated)', input: 'text' },
    { key: 'status', label: 'Status', input: 'select', options: ['ACTIVE', 'CLOSED'] },
  ],
  columns: [
    { key: 'id', label: 'ID', render: (r) => r.id },
    { key: 'name', label: 'Name', render: (r) => r.name },
    { key: 'capacity', label: 'Capacity', render: (r) => String(r.capacity) },
    { key: 'status', label: 'Status', render: (r) => r.status },
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
  title: 'School Days',
  fields: [
    { key: 'weekday', label: 'Weekday', input: 'select', options: WEEKDAYS },
    { key: 'is_active', label: 'Active', input: 'checkbox' },
  ],
  columns: [
    { key: 'id', label: 'ID', render: (d) => d.id },
    { key: 'weekday', label: 'Weekday', render: (d) => d.weekday },
    { key: 'is_active', label: 'Active', render: (d) => (d.is_active ? 'Yes' : 'No') },
  ],
  toFormState: (d) => ({ weekday: d.weekday, is_active: d.is_active ? 'true' : 'false' }),
  emptyFormState: { weekday: 'MONDAY', is_active: 'true' },
  toUpsert: (form) => ({
    weekday: (form.weekday || 'MONDAY') as SchoolDayUpsertRequest['weekday'],
    is_active: form.is_active === 'true',
  }),
}

export const timePeriodConfig: EntityManagerConfig<TimePeriod, TimePeriodUpsertRequest> = {
  title: 'Time Periods',
  fields: [
    { key: 'index', label: 'Order index', input: 'number' },
    { key: 'start_time', label: 'Start time (HH:MM:SS)', input: 'text' },
    { key: 'end_time', label: 'End time (HH:MM:SS)', input: 'text' },
    { key: 'kind', label: 'Kind', input: 'select', options: ['LESSON', 'BREAK'] },
  ],
  columns: [
    { key: 'id', label: 'ID', render: (p) => p.id },
    { key: 'index', label: 'Order', render: (p) => String(p.index) },
    { key: 'time', label: 'Time', render: (p) => `${p.start_time}–${p.end_time}` },
    { key: 'kind', label: 'Kind', render: (p) => p.kind },
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
  title: 'Lesson Requirements',
  fields: [
    { key: 'class_id', label: 'Class ID', input: 'text' },
    { key: 'subject_id', label: 'Subject ID', input: 'text' },
    { key: 'weekly_periods', label: 'Weekly periods', input: 'number' },
    { key: 'required_capability', label: 'Required room capability (optional)', input: 'text' },
  ],
  columns: [
    { key: 'id', label: 'ID', render: (r) => r.id },
    { key: 'class_id', label: 'Class', render: (r) => r.class_id },
    { key: 'subject_id', label: 'Subject', render: (r) => r.subject_id },
    { key: 'weekly_periods', label: 'Weekly periods', render: (r) => String(r.weekly_periods) },
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
