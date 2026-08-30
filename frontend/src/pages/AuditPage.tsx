import { useState } from 'react'
import { useAuditForEntity } from '../hooks/useAudit'
import type { AuditEntityType } from '../types/enums'

const ENTITY_TYPES: AuditEntityType[] = [
  'SCHOOL',
  'TEACHER',
  'CLASS',
  'SUBJECT',
  'ROOM',
  'LESSON_REQUIREMENT',
  'AVAILABILITY',
  'SCHEDULE',
  'SCHEDULE_VERSION',
  'SCHEDULE_ASSIGNMENT',
  'SCHEDULING_CONFIG',
  'USER',
]

export function AuditPage() {
  const [entityType, setEntityType] = useState<AuditEntityType>('SCHEDULE_VERSION')
  const [entityId, setEntityId] = useState('')
  const [submittedId, setSubmittedId] = useState('')

  const { data: events, isFetching } = useAuditForEntity(entityType, submittedId || undefined)

  return (
    <main>
      <h2>Audit Log</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          setSubmittedId(entityId)
        }}
      >
        <label htmlFor="audit-entity-type">Entity type</label>
        <select
          id="audit-entity-type"
          value={entityType}
          onChange={(e) => setEntityType(e.target.value as AuditEntityType)}
        >
          {ENTITY_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>

        <label htmlFor="audit-entity-id">Entity ID</label>
        <input
          id="audit-entity-id"
          value={entityId}
          onChange={(e) => setEntityId(e.target.value)}
        />

        <button type="submit">Search</button>
      </form>

      {isFetching && <p>Loading…</p>}
      {events && (
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Operation</th>
              <th>Actor</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.id}>
                <td>{new Date(event.timestamp).toLocaleString()}</td>
                <td>{event.operation}</td>
                <td>
                  {event.actor.user_id} ({event.actor.role})
                </td>
                <td>{event.reason ?? '—'}</td>
              </tr>
            ))}
            {events.length === 0 && (
              <tr>
                <td colSpan={4}>No audit events found.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </main>
  )
}
