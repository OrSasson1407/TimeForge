import { useReschedulingEvents } from '../../hooks/useRescheduling'

export function ReschedulingEventsList({ schoolId }: { schoolId: string }) {
  const { data: events } = useReschedulingEvents(schoolId)

  return (
    <section>
      <h3>Disruption history</h3>
      <table>
        <thead>
          <tr>
            <th>Reported</th>
            <th>Type</th>
            <th>Target</th>
            <th>Affected slots</th>
            <th>Reason</th>
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
              <td colSpan={5}>No disruptions reported yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  )
}
