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
import { useLanguage } from '../../state/LanguageContext'
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
  const { t } = useLanguage()
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
      <h3>{t('disruption.title')}</h3>

      <label htmlFor="disruption-event-type">{t('disruption.whatUnavailable')}</label>
      <select
        id="disruption-event-type"
        value={eventType}
        onChange={(e) => {
          setEventType(e.target.value as ReschedulingEventType)
          setTargetId('')
        }}
      >
        <option value="TEACHER_UNAVAILABLE">{t('disruption.aTeacher')}</option>
        <option value="ROOM_UNAVAILABLE">{t('disruption.aRoom')}</option>
      </select>

      <label htmlFor="disruption-target">
        {eventType === 'TEACHER_UNAVAILABLE' ? t('disruption.teacher') : t('disruption.room')}
      </label>
      <select id="disruption-target" value={targetId} onChange={(e) => setTargetId(e.target.value)}>
        <option value="">{t('disruption.select')}</option>
        {targetOptions.map((entity) => (
          <option key={entity.id} value={entity.id}>
            {entity.name}
          </option>
        ))}
      </select>

      <fieldset>
        <legend>{t('disruption.affectedSlots')}</legend>
        <table>
          <thead>
            <tr>
              <th>{t('disruption.period')}</th>
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

      <label htmlFor="disruption-reason">{t('disruption.reason')}</label>
      <input id="disruption-reason" value={reason} onChange={(e) => setReason(e.target.value)} />

      <button
        type="button"
        onClick={handleSubmit}
        disabled={report.isPending || !targetId || selectedSlots.size === 0 || !reason}
      >
        {report.isPending ? t('disruption.submitting') : t('disruption.submit')}
      </button>

      {report.data && (
        <div role="status">
          <p>{t('disruption.result', { status: report.data.status })}</p>
          {report.data.status === 'REPAIRED' && report.data.disruption_cost && (
            <p>
              {t('disruption.repaired', {
                moved: report.data.disruption_cost.moved_assignments,
                rooms: report.data.disruption_cost.changed_rooms,
                teachers: report.data.disruption_cost.changed_teachers,
              })}
            </p>
          )}
          {report.data.status === 'UNREPAIRABLE' && report.data.infeasibility && (
            <div>
              <p>{report.data.infeasibility.note ?? t('disruption.noRepairFound')}</p>
              <ul>
                {report.data.infeasibility.bottlenecks.map((b, i) => (
                  <li key={i}>
                    {t('disruption.bottleneckLine', {
                      subject: b.subject_id,
                      required: b.required,
                      available: b.available,
                    })}
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
