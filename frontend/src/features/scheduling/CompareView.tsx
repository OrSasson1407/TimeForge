import { useState } from 'react'
import { useCompareVersions, useScheduleVersions } from '../../hooks/useSchedule'
import type { AssignmentDiffEntry } from '../../types/schedule'

function DiffList({ title, entries }: { title: string; entries: AssignmentDiffEntry[] }) {
  if (entries.length === 0) return null
  return (
    <div>
      <h4>
        {title} ({entries.length})
      </h4>
      <ul>
        {entries.map((entry) => (
          <li key={entry.lesson_id}>
            Lesson {entry.lesson_id}:{' '}
            {entry.before ? `${entry.before.day_id}/${entry.before.time_period_id}` : 'unassigned'}{' '}
            → {entry.after ? `${entry.after.day_id}/${entry.after.time_period_id}` : 'unassigned'}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function CompareView({ schoolId }: { schoolId: string }) {
  const { data: versions } = useScheduleVersions(schoolId)
  const [fromId, setFromId] = useState('')
  const [toId, setToId] = useState('')
  const { data: diff } = useCompareVersions(schoolId, fromId || undefined, toId || undefined)

  return (
    <section>
      <h3>Compare versions</h3>
      <label htmlFor="compare-from">From</label>
      <select id="compare-from" value={fromId} onChange={(e) => setFromId(e.target.value)}>
        <option value="">Select…</option>
        {versions?.map((v) => (
          <option key={v.id} value={v.id}>
            {v.id} ({v.status})
          </option>
        ))}
      </select>

      <label htmlFor="compare-to">To</label>
      <select id="compare-to" value={toId} onChange={(e) => setToId(e.target.value)}>
        <option value="">Select…</option>
        {versions?.map((v) => (
          <option key={v.id} value={v.id}>
            {v.id} ({v.status})
          </option>
        ))}
      </select>

      {diff && (
        <div>
          <p>{diff.unchanged_count} assignments unchanged.</p>
          <DiffList title="Added" entries={diff.added} />
          <DiffList title="Removed" entries={diff.removed} />
          <DiffList title="Moved" entries={diff.moved} />
          {diff.added.length === 0 && diff.removed.length === 0 && diff.moved.length === 0 && (
            <p>No differences.</p>
          )}
        </div>
      )}
    </section>
  )
}
