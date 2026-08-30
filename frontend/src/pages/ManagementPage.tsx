import { useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'
import type { TranslationKey } from '../i18n/translations'
import { EntityManager } from '../features/management/EntityManager'
import { TeacherCsvImport } from '../features/management/TeacherCsvImport'
import {
  classConfig,
  lessonRequirementConfig,
  roomConfig,
  schoolDayConfig,
  subjectConfig,
  teacherConfig,
  timePeriodConfig,
} from '../features/management/entityConfigs'
import {
  classHooks,
  lessonRequirementHooks,
  roomHooks,
  schoolDayHooks,
  subjectHooks,
  teacherHooks,
  timePeriodHooks,
} from '../hooks/useCatalog'

const TABS = [
  'Teachers',
  'Classes',
  'Subjects',
  'Rooms',
  'School Days',
  'Time Periods',
  'Lesson Requirements',
] as const

type Tab = (typeof TABS)[number]

const TAB_TITLE_KEY: Record<Tab, TranslationKey> = {
  Teachers: 'catalog.teachers.title',
  Classes: 'catalog.classes.title',
  Subjects: 'catalog.subjects.title',
  Rooms: 'catalog.rooms.title',
  'School Days': 'catalog.schoolDays.title',
  'Time Periods': 'catalog.timePeriods.title',
  'Lesson Requirements': 'catalog.lessonRequirements.title',
}

export function ManagementPage() {
  const { user } = useAuth()
  const { t } = useLanguage()
  const [tab, setTab] = useState<Tab>('Teachers')
  const schoolId = user?.school_id

  return (
    <div>
      <h2>{t('management.title')}</h2>
      <nav aria-label={t('management.sectionsAriaLabel')}>
        {TABS.map((tabName) => (
          <button
            type="button"
            key={tabName}
            onClick={() => setTab(tabName)}
            aria-current={tab === tabName ? 'true' : undefined}
          >
            {t(TAB_TITLE_KEY[tabName])}
          </button>
        ))}
      </nav>

      {tab === 'Teachers' && <TeachersTab schoolId={schoolId} />}
      {tab === 'Classes' && <ClassesTab schoolId={schoolId} />}
      {tab === 'Subjects' && <SubjectsTab schoolId={schoolId} />}
      {tab === 'Rooms' && <RoomsTab schoolId={schoolId} />}
      {tab === 'School Days' && <SchoolDaysTab schoolId={schoolId} />}
      {tab === 'Time Periods' && <TimePeriodsTab schoolId={schoolId} />}
      {tab === 'Lesson Requirements' && <LessonRequirementsTab schoolId={schoolId} />}
    </div>
  )
}

function TeachersTab({ schoolId }: { schoolId: string | undefined }) {
  const { data } = teacherHooks.useList(schoolId)
  const upsert = teacherHooks.useUpsert(schoolId)
  return (
    <>
      <TeacherCsvImport onImport={(id, body) => upsert.mutateAsync({ id, body })} />
      <EntityManager
        config={teacherConfig}
        entities={data ?? []}
        isSaving={upsert.isPending}
        saveError={upsert.error instanceof Error ? upsert.error.message : null}
        onSave={(id, body) => upsert.mutate({ id, body })}
      />
    </>
  )
}

function ClassesTab({ schoolId }: { schoolId: string | undefined }) {
  const { data } = classHooks.useList(schoolId)
  const upsert = classHooks.useUpsert(schoolId)
  return (
    <EntityManager
      config={classConfig}
      entities={data ?? []}
      isSaving={upsert.isPending}
      saveError={upsert.error instanceof Error ? upsert.error.message : null}
      onSave={(id, body) => upsert.mutate({ id, body })}
    />
  )
}

function SubjectsTab({ schoolId }: { schoolId: string | undefined }) {
  const { data } = subjectHooks.useList(schoolId)
  const upsert = subjectHooks.useUpsert(schoolId)
  return (
    <EntityManager
      config={subjectConfig}
      entities={data ?? []}
      isSaving={upsert.isPending}
      saveError={upsert.error instanceof Error ? upsert.error.message : null}
      onSave={(id, body) => upsert.mutate({ id, body })}
    />
  )
}

function RoomsTab({ schoolId }: { schoolId: string | undefined }) {
  const { data } = roomHooks.useList(schoolId)
  const upsert = roomHooks.useUpsert(schoolId)
  return (
    <EntityManager
      config={roomConfig}
      entities={data ?? []}
      isSaving={upsert.isPending}
      saveError={upsert.error instanceof Error ? upsert.error.message : null}
      onSave={(id, body) => upsert.mutate({ id, body })}
    />
  )
}

function SchoolDaysTab({ schoolId }: { schoolId: string | undefined }) {
  const { data } = schoolDayHooks.useList(schoolId)
  const upsert = schoolDayHooks.useUpsert(schoolId)
  return (
    <EntityManager
      config={schoolDayConfig}
      entities={data ?? []}
      isSaving={upsert.isPending}
      saveError={upsert.error instanceof Error ? upsert.error.message : null}
      onSave={(id, body) => upsert.mutate({ id, body })}
    />
  )
}

function TimePeriodsTab({ schoolId }: { schoolId: string | undefined }) {
  const { data } = timePeriodHooks.useList(schoolId)
  const upsert = timePeriodHooks.useUpsert(schoolId)
  return (
    <EntityManager
      config={timePeriodConfig}
      entities={data ?? []}
      isSaving={upsert.isPending}
      saveError={upsert.error instanceof Error ? upsert.error.message : null}
      onSave={(id, body) => upsert.mutate({ id, body })}
    />
  )
}

function LessonRequirementsTab({ schoolId }: { schoolId: string | undefined }) {
  const { data } = lessonRequirementHooks.useList(schoolId)
  const upsert = lessonRequirementHooks.useUpsert(schoolId)
  return (
    <EntityManager
      config={lessonRequirementConfig}
      entities={data ?? []}
      isSaving={upsert.isPending}
      saveError={upsert.error instanceof Error ? upsert.error.message : null}
      onSave={(id, body) => upsert.mutate({ id, body })}
    />
  )
}
