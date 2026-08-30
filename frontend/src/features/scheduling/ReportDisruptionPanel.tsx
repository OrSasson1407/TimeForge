/**
 * FR-020/FR-021/FR-022: report a disruption (a teacher or room becoming
 * unavailable at specific slots) and trigger a repair. Only
 * TEACHER_UNAVAILABLE/ROOM_UNAVAILABLE are offered — the other
 * `ReschedulingEventType` values exist on the backend enum for
 * extensibility but aren't implemented yet (docs/04-DESIGN.md #17's
 * "Implemented event types" note), so offering them here would be a
 * misleading affordance for a feature that doesn't actually work.
 */
import { useState } from 'react'
import { useReportDisruption } from '../../hooks/useRescheduling'
import type { ReschedulingEventType } from '../../types/rescheduling'
import type { SchoolDay, TimePeriod, Teacher, Room } from '../../types/catalog'

interface ReportDisruptionPanelProps {
  schoolId: string
  days: SchoolDay[]
  periods: TimePeriod[]
  teachers: Teacher[]
  rooms: Room[]
  onRepaired: (versionId: string) => void
}

export function ReportDisruptionPanel({
  schoolId,
  days,
  periods,
  teachers,
  rooms,
  onRepaired,
}: ReportDisruptionPanelProps) {
  const [eventType, setEventType] = useState<ReschedulingEventType>('TEACHER_UNAVAILABLE')
  const [targetId, setTargetId] = useState('')
  const [reason, setReason] = useState('')
  const [selectedSlots, setSelectedSlots] = useState<Set<string>>(new Set())

  const report = useReportDisruption(schoolId)
  const activeDays = days.filter((d) => d.is_active)
  const lessonPeriods = periods.filter((p) => p.kind === 'LESSON').sort((a, b) => a.index - b.index)
  const targetOptions = eventType === 'TEACHER_UNAVAILABLE' ? teachers : rooms

  function slotKey(dayId: string, periodId: string): string {
    return `${dayId}:${periodId}`
  }

  function toggleSlot(dayId: string, periodId: string) {
    const key = slotKey(dayId, periodId)
    setSelectedSlots((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  function handleSubmit() {
    if (!targetId || selectedSlots.size === 0 || !reason) return
    report.mutate(
      {
        request_id: crypto.randomUUID(),
        event_type: eventType,
        target_entity_id: targetId,
        affected_slots: [...selectedSlots].map((key) => {
          const [dayId, periodId] = key.split(':')
          return { day_id: dayId, time_period_id: periodId }
        }),
        reason,
      },
      {
        onSuccess: (result) => {
          if (result.version) onRepaired(result.version.id)
        },
      },
    )
  }

  return (
    <section>
      <h3>Report a disruption</h3>

      <label htmlFor="disruption-event-type">What became unavailable</label>
      <select
        id="disruption-event-type"
        value={eventType}
        onChange={(e) => {
          setEventType(e.target.value as ReschedulingEventType)
          setTargetId('')
        }}
      >
        <option value="TEACHER_UNAVAILABLE">A teacher</option>
        <option value="ROOM_UNAVAILABLE">A room</option>
      </select>

      <label htmlFor="disruption-target">
        {eventType === 'TEACHER_UNAVAILABLE' ? 'Teacher' : 'Room'}
      </label>
      <select id="disruption-target" value={targetId} onChange={(e) => setTargetId(e.target.value)}>
        <option value="">Select…</option>
        {targetOptions.map((entity) => (
          <option key={entity.id} value={entity.id}>
            {entity.name}
          </option>
        ))}
      </select>

      <fieldset>
        <legend>Affected slots</legend>
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
                {activeDays.map((day) => (
                  <td key={day.id}>
                    <input
                      type="checkbox"
                      aria-label={`${day.weekday} ${period.start_time}`}
                      checked={selectedSlots.has(slotKey(day.id, period.id))}
                      onChange={() => toggleSlot(day.id, period.id)}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </fieldset>

      <label htmlFor="disruption-reason">Reason</label>
      <input id="disruption-reason" value={reason} onChange={(e) => setReason(e.target.value)} />

      <button
        type="button"
        onClick={handleSubmit}
        disabled={report.isPending || !targetId || selectedSlots.size === 0 || !reason}
      >
        {report.isPending ? 'Repairing…' : 'Report and repair'}
      </button>

      {report.data && (
        <div role="status">
          <p>Result: {report.data.status}</p>
          {report.data.status === 'REPAIRED' && report.data.disruption_cost && (
            <p>
              Repaired — {report.data.disruption_cost.moved_assignments} moved,{' '}
              {report.data.disruption_cost.changed_rooms} room change(s),{' '}
              {report.data.disruption_cost.changed_teachers} teacher change(s).
            </p>
          )}
          {report.data.status === 'UNREPAIRABLE' && report.data.infeasibility && (
            <div>
              <p>{report.data.infeasibility.note ?? 'No repair could be found.'}</p>
              <ul>
                {report.data.infeasibility.bottlenecks.map((b, i) => (
                  <li key={i}>
                    {b.subject_id}: needs {b.required}, only {b.available} available.
                  </li>
                ))}
              </ul>
            </div>
          )}
          {report.data.status === 'FAILED' && <p>{report.data.error}</p>}
        </div>
      )}
      {report.isError && <p role="alert">{(report.error as Error).message}</p>}
    </section>
  )
}
