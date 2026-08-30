/**
 * A day x period grid of availability toggles for one owner (a Teacher or a
 * Class). Each cell writes exactly one day-specific Availability record
 * (`day_id` always set) — day-independent records ("unavailable on this
 * period every day") are a real part of the domain model
 * (docs/04-DESIGN.md Availability decision) but this editor doesn't create
 * them; a day-independent record still displays correctly here (its
 * `is_available` value applies to every day's cell for that period until a
 * day-specific override exists), it just isn't how this UI writes changes.
 */
import type { OwnerType } from '../../types/enums'
import type { Availability } from '../../types/availability'
import type { SchoolDay } from '../../types/catalog'
import type { TimePeriod } from '../../types/catalog'
import { useUpsertAvailability } from '../../hooks/useAvailability'
import { useLanguage } from '../../state/LanguageContext'

interface AvailabilityGridProps {
  schoolId: string
  ownerType: OwnerType
  ownerId: string
  days: SchoolDay[]
  periods: TimePeriod[]
  records: Availability[]
  readOnly?: boolean
}

function recordFor(
  records: Availability[],
  dayId: string,
  periodId: string,
): Availability | undefined {
  return (
    records.find((r) => r.day_id === dayId && r.time_period_id === periodId) ??
    records.find((r) => r.day_id === null && r.time_period_id === periodId)
  )
}

export function AvailabilityGrid({
  schoolId,
  ownerType,
  ownerId,
  days,
  periods,
  records,
  readOnly = false,
}: AvailabilityGridProps) {
  const { t } = useLanguage()
  const upsert = useUpsertAvailability(schoolId)
  const lessonPeriods = periods.filter((p) => p.kind === 'LESSON').sort((a, b) => a.index - b.index)
  const activeDays = days.filter((d) => d.is_active)

  function toggle(day: SchoolDay, period: TimePeriod) {
    const existing = records.find((r) => r.day_id === day.id && r.time_period_id === period.id)
    const nextAvailable = existing ? !existing.is_available : false
    const id = `avail_${ownerType.toLowerCase()}_${ownerId}_${day.id}_${period.id}`
    upsert.mutate({
      id,
      body: {
        owner_type: ownerType,
        owner_id: ownerId,
        day_id: day.id,
        time_period_id: period.id,
        is_available: nextAvailable,
        preference_weight: existing?.preference_weight ?? 0,
      },
    })
  }

  return (
    <table>
      <thead>
        <tr>
          <th>{t('availability.period')}</th>
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
              const record = recordFor(records, day.id, period.id)
              const available = record?.is_available ?? true
              return (
                <td key={day.id}>
                  <button
                    type="button"
                    disabled={readOnly || upsert.isPending}
                    aria-pressed={available}
                    onClick={() => toggle(day, period)}
                  >
                    {available ? t('availability.available') : t('availability.unavailable')}
                  </button>
                </td>
              )
            })}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
