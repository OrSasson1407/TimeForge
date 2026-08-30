import { useMemo, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import {
  classHooks,
  roomHooks,
  schoolDayHooks,
  teacherHooks,
  timePeriodHooks,
} from '../hooks/useCatalog'
import { useSchedule, useScheduleAssignments, useScheduleVersion } from '../hooks/useSchedule'
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

  const [viewBy, setViewBy] = useState<TimetableView>(isAdmin ? 'class' : 'teacher')
  const [viewId, setViewId] = useState<string>(isAdmin ? '' : (user?.teacher_id ?? ''))
  const [movingAssignment, setMovingAssignment] = useState<ScheduleAssignment | null>(null)

  const teacherNames = useMemo(() => nameMap(teachers), [teachers])
  const classNames = useMemo(() => nameMap(classes), [classes])
  const roomNames = useMemo(() => nameMap(rooms), [rooms])

  const viewOptions = viewBy === 'class' ? classes : viewBy === 'teacher' ? teachers : rooms

  return (
    <main>
      <h2>Schedule</h2>

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
            ? 'Showing the currently published schedule.'
            : 'No schedule has been published yet.'}
        </p>
      )}

      <section>
        <h3>Timetable</h3>
        <label htmlFor="timetable-view-by">View by</label>
        <select
          id="timetable-view-by"
          value={viewBy}
          onChange={(e) => {
            setViewBy(e.target.value as TimetableView)
            setViewId('')
          }}
        >
          <option value="class">Class</option>
          <option value="teacher">Teacher</option>
          <option value="room">Room</option>
        </select>

        <label htmlFor="timetable-view-id">{viewBy}</label>
        <select id="timetable-view-id" value={viewId} onChange={(e) => setViewId(e.target.value)}>
          <option value="">Select…</option>
          {viewOptions?.map((entity) => (
            <option key={entity.id} value={entity.id}>
              {entity.name}
            </option>
          ))}
        </select>

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
            onSelectAssignment={
              isAdmin && version.status === 'DRAFT' ? (a) => setMovingAssignment(a) : undefined
            }
          />
        ) : (
          <p>
            {effectiveVersionId
              ? 'Select what to view.'
              : isAdmin
                ? 'Generate or select a version above.'
                : 'Nothing to show yet.'}
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
