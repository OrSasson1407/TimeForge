import { useScheduleVersions, usePublishVersion } from '../../hooks/useSchedule'
import type { ScheduleVersion } from '../../types/schedule'

interface VersionPickerProps {
  schoolId: string
  selectedVersionId: string | null
  onSelect: (versionId: string) => void
}

export function VersionPicker({ schoolId, selectedVersionId, onSelect }: VersionPickerProps) {
  const { data: versions } = useScheduleVersions(schoolId)
  const publish = usePublishVersion(schoolId, selectedVersionId ?? undefined)
  const selected = versions?.find((v) => v.id === selectedVersionId)

  return (
    <section>
      <h3>Versions</h3>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Status</th>
            <th>Created</th>
            <th>Quality</th>
            <th>Hard violations</th>
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
                  {selectedVersionId === version.id ? 'Selected' : 'View'}
                </button>
              </td>
            </tr>
          ))}
          {versions && versions.length === 0 && (
            <tr>
              <td colSpan={6}>No versions yet — generate one above.</td>
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
            {publish.isPending ? 'Publishing…' : 'Publish this version'}
          </button>
          {(selected.score?.hard_violations ?? 1) > 0 && (
            <p>This version still has hard-constraint violations and cannot be published.</p>
          )}
          {publish.isError && <p role="alert">{(publish.error as Error).message}</p>}
        </div>
      )}
    </section>
  )
}
