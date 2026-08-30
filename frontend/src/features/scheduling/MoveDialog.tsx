/**
 * FR-014/FR-015: propose a move, get a server-side VALID/WARNING/INVALID
 * verdict, and only then may it be applied — the frontend never decides a
 * move is valid on its own (docs/01-CLAUDE.md rule 11). Apply always
 * re-validates against the exact form values that were last checked, so a
 * change to the form after validating (but before applying) can't slip
 * through unchecked.
 */
import { useState } from 'react'
import { useApplyMove, useValidateMove } from '../../hooks/useSchedule'
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
  const [form, setForm] = useState<MoveForm>({
    teacherId: assignment.teacher_id,
    roomId: assignment.room_id,
    dayId: assignment.day_id,
    periodId: assignment.time_period_id,
  })
  const [validatedFor, setValidatedFor] = useState<MoveForm | null>(null)

  const validateMove = useValidateMove(schoolId, version.id)
  const applyMove = useApplyMove(schoolId, version.id)

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
    applyMove.mutate(
      {
        assignment_id: assignment.id,
        teacher_id: form.teacherId,
        room_id: form.roomId,
        day_id: form.dayId,
        time_period_id: form.periodId,
        expected_version_tag: version.version_tag,
      },
      { onSuccess: onClose },
    )
  }

  return (
    <dialog open aria-label="Move assignment">
      <h3>Move assignment</h3>

      <label htmlFor="move-teacher">Teacher</label>
      <select
        id="move-teacher"
        value={form.teacherId}
        onChange={(e) => setForm({ ...form, teacherId: e.target.value })}
      >
        {teachers.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>

      <label htmlFor="move-room">Room</label>
      <select
        id="move-room"
        value={form.roomId}
        onChange={(e) => setForm({ ...form, roomId: e.target.value })}
      >
        {rooms.map((r) => (
          <option key={r.id} value={r.id}>
            {r.name}
          </option>
        ))}
      </select>

      <label htmlFor="move-day">Day</label>
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

      <label htmlFor="move-period">Period</label>
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
          {validateMove.isPending ? 'Validating…' : 'Validate'}
        </button>
        <button type="button" onClick={handleApply} disabled={!canApply || applyMove.isPending}>
          {applyMove.isPending ? 'Applying…' : 'Apply'}
        </button>
        <button type="button" onClick={onClose}>
          Cancel
        </button>
      </div>

      {validateMove.data && (
        <p role="status">
          {validateMove.data.result}
          {validateMove.data.message ? `: ${validateMove.data.message}` : ''}
        </p>
      )}
      {applyMove.isError && <p role="alert">{(applyMove.error as Error).message}</p>}
    </dialog>
  )
}
