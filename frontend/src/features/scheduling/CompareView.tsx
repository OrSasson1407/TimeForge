import { useState } from 'react'
import { useCompareVersions, useScheduleVersions } from '../../hooks/useSchedule'
import { useLanguage } from '../../state/LanguageContext'
import type { AssignmentDiffEntry } from '../../types/schedule'

function DiffList({ title, entries }: { title: string; entries: AssignmentDiffEntry[] }) {
  const { t } = useLanguage()
  if (entries.length === 0) return null
  return (
    <div>
      <h4>
        {title} ({entries.length})
      </h4>
      <ul>
        {entries.map((entry) => (
          <li key={entry.lesson_id}>
            {t('compare.lessonLine', {
              id: entry.lesson_id,
              before: entry.before
                ? `${entry.before.day_id}/${entry.before.time_period_id}`
                : t('compare.unassigned'),
              after: entry.after
                ? `${entry.after.day_id}/${entry.after.time_period_id}`
                : t('compare.unassigned'),
            })}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function CompareView({ schoolId }: { schoolId: string }) {
  const { t } = useLanguage()
  const { data: versions } = useScheduleVersions(schoolId)
  const [fromId, setFromId] = useState('')
  const [toId, setToId] = useState('')
  const { data: diff } = useCompareVersions(schoolId, fromId || undefined, toId || undefined)

  return (
    <section>
      <h3>{t('compare.title')}</h3>
      <label htmlFor="compare-from">{t('compare.from')}</label>
      <select id="compare-from" value={fromId} onChange={(e) => setFromId(e.target.value)}>
        <option value="">{t('compare.select')}</option>
        {versions?.map((v) => (
          <option key={v.id} value={v.id}>
            {v.id} ({v.status})
          </option>
        ))}
      </select>

      <label htmlFor="compare-to">{t('compare.to')}</label>
      <select id="compare-to" value={toId} onChange={(e) => setToId(e.target.value)}>
        <option value="">{t('compare.select')}</option>
        {versions?.map((v) => (
          <option key={v.id} value={v.id}>
            {v.id} ({v.status})
          </option>
        ))}
      </select>

      {diff && (
        <div>
          <p>{t('compare.unchanged', { count: diff.unchanged_count })}</p>
          <DiffList title={t('compare.added')} entries={diff.added} />
          <DiffList title={t('compare.removed')} entries={diff.removed} />
          <DiffList title={t('compare.moved')} entries={diff.moved} />
          {diff.added.length === 0 && diff.removed.length === 0 && diff.moved.length === 0 && (
            <p>{t('compare.noDifferences')}</p>
          )}
        </div>
      )}
    </section>
  )
}
