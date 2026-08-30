import type { SchoolDay, TimePeriod } from '../../types/catalog'
import type { ScheduleAssignment } from '../../types/schedule'

export type TimetableView = 'class' | 'teacher' | 'room'

interface TimetableGridProps {
  days: SchoolDay[]
  periods: TimePeriod[]
  assignments: ScheduleAssignment[]
  viewBy: TimetableView
  viewId: string
  teacherNames: Record<string, string>
  classNames: Record<string, string>
  roomNames: Record<string, string>
  onSelectAssignment?: (assignment: ScheduleAssignment) => void
}

function fieldFor(view: TimetableView): keyof ScheduleAssignment {
  if (view === 'class') return 'class_id'
  if (view === 'teacher') return 'teacher_id'
  return 'room_id'
}

/** Renders the OTHER two entities for a cell — viewing by class shows
 * teacher + room, viewing by teacher shows class + room, and so on. */
function cellLabel(
  assignment: ScheduleAssignment,
  viewBy: TimetableView,
  names: {
    teacher: Record<string, string>
    class_: Record<string, string>
    room: Record<string, string>
  },
): string {
  const parts: string[] = []
  if (viewBy !== 'class') parts.push(names.class_[assignment.class_id] ?? assignment.class_id)
  if (viewBy !== 'teacher')
    parts.push(names.teacher[assignment.teacher_id] ?? assignment.teacher_id)
  if (viewBy !== 'room') parts.push(names.room[assignment.room_id] ?? assignment.room_id)
  return parts.join(' · ')
}

export function TimetableGrid({
  days,
  periods,
  assignments,
  viewBy,
  viewId,
  teacherNames,
  classNames,
  roomNames,
  onSelectAssignment,
}: TimetableGridProps) {
  const field = fieldFor(viewBy)
  const relevant = assignments.filter((a) => a[field] === viewId)
  const activeDays = days.filter((d) => d.is_active)
  const lessonPeriods = periods.filter((p) => p.kind === 'LESSON').sort((a, b) => a.index - b.index)

  function assignmentAt(dayId: string, periodId: string) {
    return relevant.find((a) => a.day_id === dayId && a.time_period_id === periodId)
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Period</th>
          {activeDays.map((day) => (
            <th key={day.id}>{day.weekday}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {lessonPeriods.map((period) => (
          <tr key={period.id}>
            <td>
              {period.start_time}–{period.end_time}
            </td>
            {activeDays.map((day) => {
              const assignment = assignmentAt(day.id, period.id)
              return (
                <td key={day.id}>
                  {assignment ? (
                    onSelectAssignment ? (
                      <button type="button" onClick={() => onSelectAssignment(assignment)}>
                        {cellLabel(assignment, viewBy, {
                          teacher: teacherNames,
                          class_: classNames,
                          room: roomNames,
                        })}
                      </button>
                    ) : (
                      cellLabel(assignment, viewBy, {
                        teacher: teacherNames,
                        class_: classNames,
                        room: roomNames,
                      })
                    )
                  ) : (
                    '—'
                  )}
                </td>
              )
            })}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
