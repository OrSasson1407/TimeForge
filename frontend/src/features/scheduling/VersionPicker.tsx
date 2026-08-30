import { useScheduleVersions, usePublishVersion } from '../../hooks/useSchedule'
import { useLanguage } from '../../state/LanguageContext'
import type { ScheduleVersion } from '../../types/schedule'

interface VersionPickerProps {
  schoolId: string
  selectedVersionId: string | null
  onSelect: (versionId: string) => void
}

export function VersionPicker({ schoolId, selectedVersionId, onSelect }: VersionPickerProps) {
  const { t } = useLanguage()
  const { data: versions } = useScheduleVersions(schoolId)
  const publish = usePublishVersion(schoolId, selectedVersionId ?? undefined)
  const selected = versions?.find((v) => v.id === selectedVersionId)

  return (
    <section>
      <h3>{t('versions.title')}</h3>
      <table>
        <thead>
          <tr>
            <th>{t('versions.id')}</th>
            <th>{t('versions.status')}</th>
            <th>{t('versions.created')}</th>
            <th>{t('versions.quality')}</th>
            <th>{t('versions.hardViolations')}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {(versions ?? []).map((version: ScheduleVersion) => (
            <tr key={version.id}>
              <td>{version.id}</td>
              <td>{version.status}</td>
              <td>{new Date(version.created_at).toLocaleString()}</td>
              <td>{version.score ? version.score.quality.toFixed(1) : '—'}</td>
              <td>{version.score ? version.score.hard_violations : '—'}</td>
              <td>
                <button type="button" onClick={() => onSelect(version.id)}>
                  {selectedVersionId === version.id ? t('versions.selected') : t('versions.view')}
                </button>
              </td>
            </tr>
          ))}
          {versions && versions.length === 0 && (
            <tr>
              <td colSpan={6}>{t('versions.empty')}</td>
            </tr>
          )}
        </tbody>
      </table>

      {selected && selected.status === 'DRAFT' && (
        <div>
          <button
            type="button"
            disabled={publish.isPending || (selected.score?.hard_violations ?? 1) > 0}
            onClick={() => publish.mutate({ expected_version_tag: selected.version_tag })}
          >
            {publish.isPending ? t('versions.publishing') : t('versions.publish')}
          </button>
          {(selected.score?.hard_violations ?? 1) > 0 && <p>{t('versions.cannotPublish')}</p>}
          {publish.isError && <p role="alert">{(publish.error as Error).message}</p>}
        </div>
      )}
    </section>
  )
}
