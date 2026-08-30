import { useState } from 'react'
import { useAuditForEntity } from '../hooks/useAudit'
import { useLanguage } from '../state/LanguageContext'
import { DataTable } from '../components/DataTable'
import type { DataTableColumn } from '../components/DataTable'
import { EmptyState, ErrorState, Spinner } from '../components/AsyncState'
import type { AuditEntityType } from '../types/enums'
import type { AuditEvent } from '../types/audit'

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
  const { t } = useLanguage()
  const [entityType, setEntityType] = useState<AuditEntityType>('SCHEDULE_VERSION')
  const [entityId, setEntityId] = useState('')
  const [submittedId, setSubmittedId] = useState('')

  const {
    data: events,
    isFetching,
    isError,
    refetch,
  } = useAuditForEntity(entityType, submittedId || undefined)

  const columns: DataTableColumn<AuditEvent>[] = [
    {
      key: 'timestamp',
      label: t('audit.timestamp'),
      render: (e) => new Date(e.timestamp).toLocaleString(),
    },
    { key: 'operation', label: t('audit.operation'), render: (e) => e.operation },
    {
      key: 'actor',
      label: t('audit.actor'),
      render: (e) => `${e.actor.user_id} (${e.actor.role})`,
    },
    { key: 'reason', label: t('audit.reason'), render: (e) => e.reason ?? '—' },
  ]

  return (
    <main>
      <h2>{t('audit.title')}</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          setSubmittedId(entityId)
        }}
      >
        <div className="field">
          <label htmlFor="audit-entity-type">{t('audit.entityType')}</label>
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
        </div>

        <div className="field">
          <label htmlFor="audit-entity-id">{t('audit.entityId')}</label>
          <input
            id="audit-entity-id"
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
          />
        </div>

        <button type="submit" className="btn btn-primary">
          {t('audit.search')}
        </button>
      </form>

      {isFetching && <Spinner label={t('common.loading')} />}
      {isError && <ErrorState message={t('audit.errorLoading')} onRetry={() => void refetch()} />}

      {!isFetching && !isError && events && events.length === 0 && submittedId && (
        <EmptyState title={t('audit.noResults')} />
      )}

      {!isFetching && !submittedId && (
        <EmptyState title={t('audit.emptyTitle')} message={t('audit.emptyMessage')} />
      )}

      {events && events.length > 0 && (
        <DataTable
          rows={events}
          columns={columns}
          getRowId={(e) => e.id}
          searchPlaceholder={t('audit.search')}
        />
      )}
    </main>
  )
}
