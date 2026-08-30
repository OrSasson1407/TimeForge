/**
 * FR-014/FR-015: propose a move, get a server-side VALID/WARNING/INVALID
 * verdict, and only then may it be applied — the frontend never decides a
 * move is valid on its own (docs/01-CLAUDE.md rule 11). Apply always
 * re-validates against the exact form values that were last checked, so a
 * change to the form after validating (but before applying) can't slip
 * through unchecked.
 */
import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useApplyMove, useValidateMove } from '../../hooks/useSchedule'
import { queryClient } from '../../app/queryClient'
import { scheduleApi } from '../../services/scheduleApi'
import { showToast } from '../../state/toastStore'
import { useLanguage } from '../../state/LanguageContext'
import { ApiError } from '../../services/apiClient'
import type { ScheduleAssignment, ScheduleVersion } from '../../types/schedule'
import type { SchoolDay, TimePeriod, Room, Teacher } from '../../types/catalog'

interface MoveDialogProps {
  schoolId: string
  version: ScheduleVersion
  assignment: ScheduleAssignment
  days: SchoolDay[]
  periods: TimePeriod[]
  teachers: Teacher[]
  rooms: Room[]
  onClose: () => void
}

interface MoveForm {
  teacherId: string
  roomId: string
  dayId: string
  periodId: string
}

function sameMove(a: MoveForm, b: MoveForm): boolean {
  return (
    a.teacherId === b.teacherId &&
    a.roomId === b.roomId &&
    a.dayId === b.dayId &&
    a.periodId === b.periodId
  )
}

export function MoveDialog({
  schoolId,
  version,
  assignment,
  days,
  periods,
  teachers,
  rooms,
  onClose,
}: MoveDialogProps) {
  const { t } = useLanguage()
  const [form, setForm] = useState<MoveForm>({
    teacherId: assignment.teacher_id,
    roomId: assignment.room_id,
    dayId: assignment.day_id,
    periodId: assignment.time_period_id,
  })
  const [validatedFor, setValidatedFor] = useState<MoveForm | null>(null)
  const dialogRef = useRef<HTMLDivElement>(null)

  const validateMove = useValidateMove(schoolId, version.id)
  const applyMove = useApplyMove(schoolId, version.id)

  useEffect(() => {
    dialogRef.current?.focus()
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const lessonPeriods = periods.filter((p) => p.kind === 'LESSON').sort((a, b) => a.index - b.index)
  const activeDays = days.filter((d) => d.is_active)

  function handleValidate() {
    setValidatedFor(form)
    validateMove.mutate({
      assignment_id: assignment.id,
      teacher_id: form.teacherId,
      room_id: form.roomId,
      day_id: form.dayId,
      time_period_id: form.periodId,
    })
  }

  const canApply =
    validatedFor !== null &&
    sameMove(validatedFor, form) &&
    validateMove.data !== undefined &&
    validateMove.data.result !== 'INVALID'

  function handleApply() {
    // Captured before the mutation fires — this is what "Undo" moves back
    // to, so it must be the assignment's state *before* this move, not the
    // (already-applied) form values.
    const previous = {
      teacher_id: assignment.teacher_id,
      room_id: assignment.room_id,
      day_id: assignment.day_id,
      time_period_id: assignment.time_period_id,
    }

    applyMove.mutate(
      {
        assignment_id: assignment.id,
        teacher_id: form.teacherId,
        room_id: form.roomId,
        day_id: form.dayId,
        time_period_id: form.periodId,
        expected_version_tag: version.version_tag,
      },
      {
        onSuccess: () => {
          showToast({
            type: 'success',
            message: t('move.applied'),
            action: { label: t('move.undo'), onClick: () => void undoMove(previous) },
          })
          onClose()
        },
      },
    )
  }

  // A plain async function rather than another useApplyMove() call — this
  // fires from the toast's action button, which outlives this dialog (it's
  // already closed by the time "Undo" might get clicked), so it can't rely
  // on a hook's mutation state. Re-validates against the *current* cached
  // version_tag (not the one closed over above) since the move that just
  // succeeded already bumped it server-side.
  async function undoMove(previous: {
    teacher_id: string
    room_id: string
    day_id: string
    time_period_id: string
  }) {
    const currentVersion = queryClient.getQueryData<ScheduleVersion>([
      'schedule-version',
      schoolId,
      version.id,
    ])
    try {
      await scheduleApi.applyMove(schoolId, version.id, {
        assignment_id: assignment.id,
        ...previous,
        expected_version_tag: currentVersion?.version_tag ?? version.version_tag + 1,
      })
      void queryClient.invalidateQueries({
        queryKey: ['schedule-assignments', schoolId, version.id],
      })
      void queryClient.invalidateQueries({ queryKey: ['schedule-version', schoolId, version.id] })
      void queryClient.invalidateQueries({ queryKey: ['schedule-versions', schoolId] })
      void queryClient.invalidateQueries({
        queryKey: ['schedule-violations', schoolId, version.id],
      })
      showToast({ type: 'success', message: t('move.undone') })
    } catch (err) {
      showToast({
        type: 'error',
        message: err instanceof ApiError ? err.message : t('move.undoFailed'),
      })
    }
  }

  return createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div
        ref={dialogRef}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="move-dialog-title"
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="move-dialog-title">{t('move.title')}</h2>
          <button
            type="button"
            className="btn-link"
            onClick={onClose}
            aria-label={t('common.close')}
          >
            ×
          </button>
        </div>

        <label htmlFor="move-teacher">{t('move.teacher')}</label>
        <select
          id="move-teacher"
          value={form.teacherId}
          onChange={(e) => setForm({ ...form, teacherId: e.target.value })}
        >
          {teachers.map((teacher) => (
            <option key={teacher.id} value={teacher.id}>
              {teacher.name}
            </option>
          ))}
        </select>

        <label htmlFor="move-room">{t('move.room')}</label>
        <select
          id="move-room"
          value={form.roomId}
          onChange={(e) => setForm({ ...form, roomId: e.target.value })}
        >
          {rooms.map((room) => (
            <option key={room.id} value={room.id}>
              {room.name}
            </option>
          ))}
        </select>

        <label htmlFor="move-day">{t('move.day')}</label>
        <select
          id="move-day"
          value={form.dayId}
          onChange={(e) => setForm({ ...form, dayId: e.target.value })}
        >
          {activeDays.map((d) => (
            <option key={d.id} value={d.id}>
              {d.weekday}
            </option>
          ))}
        </select>

        <label htmlFor="move-period">{t('move.period')}</label>
        <select
          id="move-period"
          value={form.periodId}
          onChange={(e) => setForm({ ...form, periodId: e.target.value })}
        >
          {lessonPeriods.map((p) => (
            <option key={p.id} value={p.id}>
              {p.start_time}–{p.end_time}
            </option>
          ))}
        </select>

        <div>
          <button type="button" onClick={handleValidate} disabled={validateMove.isPending}>
            {validateMove.isPending ? t('move.validating') : t('move.validate')}
          </button>
          <button type="button" onClick={handleApply} disabled={!canApply || applyMove.isPending}>
            {applyMove.isPending ? t('move.applying') : t('move.apply')}
          </button>
          <button type="button" onClick={onClose}>
            {t('move.cancel')}
          </button>
        </div>

        {validateMove.data && (
          <p role="status">
            {validateMove.data.result}
            {validateMove.data.message ? `: ${validateMove.data.message}` : ''}
          </p>
        )}
        {applyMove.isError && <p role="alert">{(applyMove.error as Error).message}</p>}
      </div>
    </div>,
    document.body,
  )
}
