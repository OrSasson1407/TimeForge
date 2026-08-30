import { useReschedulingEvents } from '../../hooks/useRescheduling'
import { useLanguage } from '../../state/LanguageContext'

export function ReschedulingEventsList({ schoolId }: { schoolId: string }) {
  const { t } = useLanguage()
  const { data: events } = useReschedulingEvents(schoolId)

  return (
    <section>
      <h3>{t('disruptionHistory.title')}</h3>
      <table>
        <thead>
          <tr>
            <th>{t('disruptionHistory.reported')}</th>
            <th>{t('disruptionHistory.type')}</th>
            <th>{t('disruptionHistory.target')}</th>
            <th>{t('disruptionHistory.affectedSlots')}</th>
            <th>{t('disruptionHistory.reason')}</th>
          </tr>
        </thead>
        <tbody>
          {(events ?? []).map((event) => (
            <tr key={event.id}>
              <td>{new Date(event.reported_at).toLocaleString()}</td>
              <td>{event.type}</td>
              <td>{event.target_entity_id}</td>
              <td>
                {event.affected_slots
                  .map((slot) => `${slot.day_id}/${slot.time_period_id}`)
                  .join(', ')}
              </td>
              <td>{event.reason}</td>
            </tr>
          ))}
          {events && events.length === 0 && (
            <tr>
              <td colSpan={5}>{t('disruptionHistory.empty')}</td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  )
}
