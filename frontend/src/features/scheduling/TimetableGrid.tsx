import { useMemo, useRef, useState } from 'react'
import type { DragEvent } from 'react'
import { useApplyMove } from '../../hooks/useSchedule'
import { scheduleApi } from '../../services/scheduleApi'
import { showToast } from '../../state/toastStore'
import { useLanguage } from '../../state/LanguageContext'
import { ApiError } from '../../services/apiClient'
import type { SchoolDay, TimePeriod } from '../../types/catalog'
import type { ScheduleAssignment, Violation } from '../../types/schedule'

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
  /** Every current hard-constraint violation for this version, from
   * `GET /schedules/versions/{id}/violations` — a full-state scan, so a
   * cell can be shown as persistently in conflict even when nobody is
   * dragging over it (e.g. a disruption made a previously-fine slot
   * invalid). Purely a rendering input: which lessons are broken is
   * always the backend's ConstraintEvaluator's call, never guessed here
   * (docs/01-CLAUDE.md rule 11). */
  violations?: Violation[]
  /** Enables drag-and-drop rescheduling (day/period only — teacher and room
   * stay put) alongside the click-to-open-dialog flow `onSelectAssignment`
   * already provides. Requires schoolId/versionId/expectedVersionTag to
   * call the same validate-then-apply endpoints MoveDialog uses — dragging
   * is just a faster way to reach the same server-validated move, never a
   * client-side shortcut around it (docs/01-CLAUDE.md rule 11). */
  dragToMove?: {
    schoolId: string
    versionId: string
    expectedVersionTag: number
  }
}

type CellStatus = 'checking' | 'VALID' | 'WARNING' | 'INVALID'

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

function cellKey(dayId: string, periodId: string): string {
  return `${dayId}_${periodId}`
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
  violations,
  dragToMove,
}: TimetableGridProps) {
  const { t } = useLanguage()
  const field = fieldFor(viewBy)
  const relevant = assignments.filter((a) => a[field] === viewId)
  const activeDays = days.filter((d) => d.is_active)
  const lessonPeriods = periods.filter((p) => p.kind === 'LESSON').sort((a, b) => a.index - b.index)

  // A violation's `involved_entities` mixes several id types (teacher,
  // room, period, lesson) without tagging which is which — but every id in
  // this app is globally unique, so checking "does this assignment's own
  // lesson_id appear anywhere in the tuple" is a reliable way to find which
  // violations touch which lesson, without the frontend re-deriving *why*.
  const violationsByLessonId = useMemo(() => {
    const map = new Map<string, Violation[]>()
    if (!violations || violations.length === 0) return map
    for (const assignment of assignments) {
      const matches = violations.filter((v) => v.involved_entities.includes(assignment.lesson_id))
      if (matches.length > 0) map.set(assignment.lesson_id, matches)
    }
    return map
  }, [violations, assignments])

  const [draggingAssignment, setDraggingAssignment] = useState<ScheduleAssignment | null>(null)
  const [cellStatus, setCellStatus] = useState<Record<string, CellStatus>>({})
  const checkedCellsRef = useRef<Set<string>>(new Set())

  const applyMove = useApplyMove(dragToMove?.schoolId, dragToMove?.versionId)

  function assignmentAt(dayId: string, periodId: string) {
    return relevant.find((a) => a.day_id === dayId && a.time_period_id === periodId)
  }

  function handleDragStart(assignment: ScheduleAssignment) {
    setDraggingAssignment(assignment)
    setCellStatus({})
    checkedCellsRef.current = new Set()
  }

  function handleDragEnd() {
    setDraggingAssignment(null)
    setCellStatus({})
    checkedCellsRef.current = new Set()
  }

  // A plain direct API call per cell, not TanStack Query's useMutation —
  // a drag sweeps over several cells in quick succession, so many of these
  // fire concurrently. useMutation's single shared mutation observer only
  // keeps the LAST call's options/callbacks (calling .mutate() again
  // overwrites them before earlier in-flight calls resolve), so every
  // resolving promise would end up updating whichever cell was hovered
  // last — a real bug this surfaced during manual testing. Each of these
  // calls owns its own promise and closes over its own `key`, so they
  // can't clobber each other. The actual move is still always
  // server-re-validated on apply regardless (see backend ApplyMoveUseCase's
  // docstring) — this is purely the hover preview, not the safety check.
  function handleDragEnter(day: SchoolDay, period: TimePeriod) {
    if (!draggingAssignment || !dragToMove) return
    if (day.id === draggingAssignment.day_id && period.id === draggingAssignment.time_period_id) {
      return // hovering the origin cell — nothing to check or show
    }
    const key = cellKey(day.id, period.id)
    if (checkedCellsRef.current.has(key)) return
    checkedCellsRef.current.add(key)

    setCellStatus((prev) => ({ ...prev, [key]: 'checking' }))
    scheduleApi
      .validateMove(dragToMove.schoolId, dragToMove.versionId, {
        assignment_id: draggingAssignment.id,
        teacher_id: draggingAssignment.teacher_id,
        room_id: draggingAssignment.room_id,
        day_id: day.id,
        time_period_id: period.id,
      })
      .then((data) => {
        setCellStatus((prev) => ({ ...prev, [key]: data.result }))
      })
      .catch(() => {
        setCellStatus((prev) => ({ ...prev, [key]: 'INVALID' }))
      })
  }

  function handleDrop(day: SchoolDay, period: TimePeriod) {
    if (!draggingAssignment || !dragToMove) return
    const dragged = draggingAssignment
    setDraggingAssignment(null)
    if (day.id === dragged.day_id && period.id === dragged.time_period_id) return

    const key = cellKey(day.id, period.id)
    const status = cellStatus[key]
    setCellStatus({})
    if (status === 'INVALID') {
      showToast({ type: 'error', message: t('move.invalidSlot') })
      return
    }

    applyMove.mutate(
      {
        assignment_id: dragged.id,
        teacher_id: dragged.teacher_id,
        room_id: dragged.room_id,
        day_id: day.id,
        time_period_id: period.id,
        expected_version_tag: dragToMove.expectedVersionTag,
      },
      {
        onSuccess: () => showToast({ type: 'success', message: t('move.moved') }),
        onError: (err) =>
          showToast({
            type: 'error',
            message: err instanceof ApiError ? err.message : t('move.moveFailed'),
          }),
      },
    )
  }

  return (
    <table>
      <thead>
        <tr>
          <th>{t('schedule.period')}</th>
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
              const key = cellKey(day.id, period.id)
              const status = cellStatus[key]
              const isDragOrigin =
                draggingAssignment !== null &&
                draggingAssignment.day_id === day.id &&
                draggingAssignment.time_period_id === period.id
              const dropClass = status
                ? status === 'checking'
                  ? 'timetable-cell-drop-checking'
                  : status === 'VALID'
                    ? 'timetable-cell-drop-valid'
                    : status === 'WARNING'
                      ? 'timetable-cell-drop-warning'
                      : 'timetable-cell-drop-invalid'
                : undefined
              const cellViolations = assignment
                ? violationsByLessonId.get(assignment.lesson_id)
                : undefined

              return (
                <td
                  key={day.id}
                  className={
                    [
                      cellViolations ? 'timetable-cell-violation' : null,
                      isDragOrigin ? 'timetable-cell-dragging' : null,
                      dropClass,
                    ]
                      .filter(Boolean)
                      .join(' ') || undefined
                  }
                  title={cellViolations?.map((v) => v.message).join('\n')}
                  onDragOver={
                    dragToMove
                      ? (e: DragEvent<HTMLTableCellElement>) => e.preventDefault()
                      : undefined
                  }
                  onDragEnter={dragToMove ? () => handleDragEnter(day, period) : undefined}
                  onDrop={
                    dragToMove
                      ? (e: DragEvent<HTMLTableCellElement>) => {
                          e.preventDefault()
                          handleDrop(day, period)
                        }
                      : undefined
                  }
                >
                  {assignment ? (
                    onSelectAssignment ? (
                      <button
                        type="button"
                        className={dragToMove ? 'timetable-cell-draggable' : undefined}
                        draggable={!!dragToMove}
                        onDragStart={dragToMove ? () => handleDragStart(assignment) : undefined}
                        onDragEnd={dragToMove ? handleDragEnd : undefined}
                        onClick={() => onSelectAssignment(assignment)}
                        aria-label={
                          cellViolations
                            ? `${cellLabel(assignment, viewBy, { teacher: teacherNames, class_: classNames, room: roomNames })}${t('move.violationSuffix', { details: cellViolations.map((v) => v.message).join('; ') })}`
                            : undefined
                        }
                      >
                        {cellViolations && (
                          <span aria-hidden="true" className="timetable-violation-icon">
                            ⚠
                          </span>
                        )}
                        {cellLabel(assignment, viewBy, {
                          teacher: teacherNames,
                          class_: classNames,
                          room: roomNames,
                        })}
                      </button>
                    ) : (
                      <>
                        {cellViolations && (
                          <span aria-hidden="true" className="timetable-violation-icon">
                            ⚠
                          </span>
                        )}
                        {cellLabel(assignment, viewBy, {
                          teacher: teacherNames,
                          class_: classNames,
                          room: roomNames,
                        })}
                      </>
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
