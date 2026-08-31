import { useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'
import { useScheduleAnalytics, useScheduleVersions } from '../hooks/useSchedule'
import { EmptyState, ErrorState, Spinner } from '../components/AsyncState'

/** A horizontal meter. Deliberately a plain styled div rather than a chart
 * library: these are all single-value "how full is this" readings, which a
 * bar communicates directly, and adding a charting dependency for them
 * would be a lot of bundle for no extra meaning. */
function Meter({ ratio, danger }: { ratio: number; danger?: boolean }) {
  const pct = Math.min(Math.max(ratio, 0), 1) * 100
  const color = danger
    ? 'var(--color-danger)'
    : ratio > 0.9
      ? 'var(--color-warning)'
      : 'var(--color-success)'
  return (
    <div
      className="analytics-meter"
      role="img"
      aria-label={`${Math.round(pct)}%`}
      title={`${Math.round(pct)}%`}
    >
      <span style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  )
}

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="auth-card" style={{ maxWidth: 'none', margin: 0, padding: '1rem 1.25rem' }}>
      <div className="label-mono">{label}</div>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 600 }}>
        {value}
      </div>
      {hint && <p className="field-hint">{hint}</p>}
    </div>
  )
}

export function AnalyticsPage() {
  const { user } = useAuth()
  const { t } = useLanguage()
  const schoolId = user?.school_id

  const { data: versions } = useScheduleVersions(schoolId)
  const [versionId, setVersionId] = useState('')
  const analytics = useScheduleAnalytics(schoolId, versionId || undefined)

  return (
    <main>
      <h2>{t('analytics.title')}</h2>
      <p>{t('analytics.subtitle')}</p>

      {versions && versions.length === 0 ? (
        <EmptyState title={t('analytics.noVersions')} />
      ) : (
        <div className="field" style={{ maxWidth: 420 }}>
          <label htmlFor="analytics-version">{t('analytics.selectVersion')}</label>
          <select
            id="analytics-version"
            value={versionId}
            onChange={(e) => setVersionId(e.target.value)}
          >
            <option value="">{t('analytics.select')}</option>
            {versions?.map((version) => (
              <option key={version.id} value={version.id}>
                {version.id} ({version.status})
              </option>
            ))}
          </select>
        </div>
      )}

      {!versionId && versions && versions.length > 0 && (
        <EmptyState title={t('analytics.selectToAnalyze')} />
      )}

      {analytics.isLoading && versionId && <Spinner label={t('common.loading')} />}
      {analytics.isError && (
        <ErrorState
          message={t('analytics.errorLoading')}
          onRetry={() => void analytics.refetch()}
        />
      )}

      {analytics.data && (
        <>
          <section style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', margin: '1.5rem 0' }}>
            <StatCard
              label={t('analytics.totalAssignments')}
              value={String(analytics.data.total_assignments)}
            />
            <StatCard
              label={t('analytics.weeklySlots')}
              value={String(analytics.data.lesson_slots_per_week)}
            />
            <StatCard
              label={t('analytics.workloadSpread')}
              value={analytics.data.workload_spread.toFixed(2)}
              hint={t('analytics.workloadSpreadHint')}
            />
          </section>

          <section>
            <h3>{t('analytics.teacherWorkload')}</h3>
            <table>
              <thead>
                <tr>
                  <th>{t('analytics.teacher')}</th>
                  <th>{t('analytics.periods')}</th>
                  <th>{t('analytics.maxLoad')}</th>
                  <th>{t('analytics.share')}</th>
                </tr>
              </thead>
              <tbody>
                {analytics.data.teacher_workloads.map((workload) => (
                  <tr key={workload.teacher_id}>
                    <td>{workload.teacher_name}</td>
                    <td>{workload.assigned_periods}</td>
                    <td>{workload.max_weekly_load}</td>
                    <td>
                      <Meter ratio={workload.load_ratio} danger={workload.load_ratio > 1} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section>
            <h3>{t('analytics.roomUtilization')}</h3>
            <table>
              <thead>
                <tr>
                  <th>{t('analytics.room')}</th>
                  <th>{t('analytics.used')}</th>
                  <th>{t('analytics.available')}</th>
                  <th>{t('analytics.utilization')}</th>
                </tr>
              </thead>
              <tbody>
                {analytics.data.room_utilizations.map((room) => (
                  <tr key={room.room_id}>
                    <td>{room.room_name}</td>
                    <td>{room.used_slots}</td>
                    <td>
                      {room.available_slots === 0 ? t('analytics.closed') : room.available_slots}
                    </td>
                    <td>
                      {room.available_slots === 0 ? '—' : <Meter ratio={room.utilization_ratio} />}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section>
            <h3>{t('analytics.classCoverage')}</h3>
            <table>
              <thead>
                <tr>
                  <th>{t('analytics.class')}</th>
                  <th>{t('analytics.scheduled')}</th>
                  <th>{t('analytics.required')}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {analytics.data.class_coverages.map((coverage) => (
                  <tr key={coverage.class_id}>
                    <td>{coverage.class_name}</td>
                    <td>{coverage.scheduled_periods}</td>
                    <td>{coverage.required_periods}</td>
                    <td
                      style={{
                        color: coverage.is_complete
                          ? 'var(--color-success)'
                          : 'var(--color-danger)',
                      }}
                    >
                      {coverage.is_complete ? t('analytics.complete') : t('analytics.incomplete')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </main>
  )
}
