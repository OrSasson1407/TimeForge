import { useMemo, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'
import {
  classHooks,
  roomHooks,
  schoolDayHooks,
  teacherHooks,
  timePeriodHooks,
} from '../hooks/useCatalog'
import {
  useSchedule,
  useScheduleAssignments,
  useScheduleVersion,
  useScheduleViolations,
} from '../hooks/useSchedule'
import { GeneratePanel } from '../features/scheduling/GeneratePanel'
import { VersionPicker } from '../features/scheduling/VersionPicker'
import { CompareView } from '../features/scheduling/CompareView'
import { MoveDialog } from '../features/scheduling/MoveDialog'
import { TimetableGrid } from '../features/scheduling/TimetableGrid'
import type { TimetableView } from '../features/scheduling/TimetableGrid'
import { ReportDisruptionPanel } from '../features/scheduling/ReportDisruptionPanel'
import { ReschedulingEventsList } from '../features/scheduling/ReschedulingEventsList'
import type { ScheduleAssignment } from '../types/schedule'

function nameMap(entities: { id: string; name: string }[] | undefined): Record<string, string> {
  return Object.fromEntries((entities ?? []).map((e) => [e.id, e.name]))
}

export function SchedulePage() {
  const { user } = useAuth()
  const { t } = useLanguage()
  const schoolId = user?.school_id
  const isAdmin = user?.role === 'ADMIN'

  const { data: days } = schoolDayHooks.useList(schoolId)
  const { data: periods } = timePeriodHooks.useList(schoolId)
  const { data: teachers } = teacherHooks.useList(schoolId)
  const { data: classes } = classHooks.useList(schoolId)
  const { data: rooms } = roomHooks.useList(schoolId)
  const { data: schedule } = useSchedule(schoolId)

  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null)
  const effectiveVersionId = isAdmin ? selectedVersionId : schedule?.active_version_id

  const { data: version } = useScheduleVersion(schoolId, effectiveVersionId ?? undefined)
  const { data: assignments } = useScheduleAssignments(schoolId, effectiveVersionId ?? undefined)
  const { data: violations } = useScheduleViolations(schoolId, effectiveVersionId ?? undefined)

  const [viewBy, setViewBy] = useState<TimetableView>(isAdmin ? 'class' : 'teacher')
  const [viewId, setViewId] = useState<string>(isAdmin ? '' : (user?.teacher_id ?? ''))
  const [movingAssignment, setMovingAssignment] = useState<ScheduleAssignment | null>(null)

  const teacherNames = useMemo(() => nameMap(teachers), [teachers])
  const classNames = useMemo(() => nameMap(classes), [classes])
  const roomNames = useMemo(() => nameMap(rooms), [rooms])

  const viewOptions = viewBy === 'class' ? classes : viewBy === 'teacher' ? teachers : rooms
  const viewByLabel =
    viewBy === 'class'
      ? t('schedule.class')
      : viewBy === 'teacher'
        ? t('schedule.teacher')
        : t('schedule.room')

  return (
    <main>
      <h2>{t('schedule.title')}</h2>

      {isAdmin && schoolId && (
        <>
          <GeneratePanel schoolId={schoolId} onGenerated={(id) => id && setSelectedVersionId(id)} />
          <VersionPicker
            schoolId={schoolId}
            selectedVersionId={selectedVersionId}
            onSelect={setSelectedVersionId}
          />
          <CompareView schoolId={schoolId} />
          {days && periods && teachers && rooms && (
            <ReportDisruptionPanel
              schoolId={schoolId}
              days={days}
              periods={periods}
              teachers={teachers}
              rooms={rooms}
              onRepaired={setSelectedVersionId}
            />
          )}
          <ReschedulingEventsList schoolId={schoolId} />
        </>
      )}

      {!isAdmin && (
        <p>
          {schedule?.active_version_id
            ? t('schedule.publishedNotice')
            : t('schedule.noPublishedNotice')}
        </p>
      )}

      <section>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h3>{t('schedule.timetable')}</h3>
          {days && periods && version && assignments && viewId && (
            <button
              type="button"
              className="btn btn-secondary no-print"
              onClick={() => window.print()}
            >
              🖨 {t('schedule.print')}
            </button>
          )}
        </div>
        <label htmlFor="timetable-view-by" className="no-print">
          {t('schedule.viewBy')}
        </label>
        <select
          id="timetable-view-by"
          className="no-print"
          value={viewBy}
          onChange={(e) => {
            setViewBy(e.target.value as TimetableView)
            setViewId('')
          }}
        >
          <option value="class">{t('schedule.class')}</option>
          <option value="teacher">{t('schedule.teacher')}</option>
          <option value="room">{t('schedule.room')}</option>
        </select>

        <label htmlFor="timetable-view-id" className="no-print">
          {viewByLabel}
        </label>
        <select
          id="timetable-view-id"
          className="no-print"
          value={viewId}
          onChange={(e) => setViewId(e.target.value)}
        >
          <option value="">{t('schedule.select')}</option>
          {viewOptions?.map((entity) => (
            <option key={entity.id} value={entity.id}>
              {entity.name}
            </option>
          ))}
        </select>

        {days && periods && version && assignments && viewId && (
          <p className="print-only" style={{ display: 'none' }}>
            {viewByLabel}: {viewOptions?.find((o) => o.id === viewId)?.name}
          </p>
        )}

        {days && periods && version && assignments && viewId ? (
          <TimetableGrid
            days={days}
            periods={periods}
            assignments={assignments}
            viewBy={viewBy}
            viewId={viewId}
            teacherNames={teacherNames}
            classNames={classNames}
            roomNames={roomNames}
            violations={violations}
            onSelectAssignment={
              isAdmin && version.status === 'DRAFT' ? (a) => setMovingAssignment(a) : undefined
            }
            dragToMove={
              isAdmin && version.status === 'DRAFT' && schoolId
                ? {
                    schoolId,
                    versionId: version.id,
                    expectedVersionTag: version.version_tag,
                  }
                : undefined
            }
          />
        ) : (
          <p>
            {effectiveVersionId
              ? t('schedule.selectWhatToView')
              : isAdmin
                ? t('schedule.generateOrSelect')
                : t('schedule.nothingToShowYet')}
          </p>
        )}
      </section>

      {movingAssignment && schoolId && version && days && periods && teachers && rooms && (
        <MoveDialog
          schoolId={schoolId}
          version={version}
          assignment={movingAssignment}
          days={days}
          periods={periods}
          teachers={teachers}
          rooms={rooms}
          onClose={() => setMovingAssignment(null)}
        />
      )}
    </main>
  )
}
