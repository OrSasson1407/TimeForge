import { useState } from 'react'
import { useGenerateSchedule } from '../../hooks/useSchedule'

interface GeneratePanelProps {
  schoolId: string
  onGenerated: (versionId: string | null) => void
}

/** FR-009/FR-010/FR-011/FR-025: triggers generation and surfaces the
 * solver's outcome plainly — VALID (with the new version id), INFEASIBLE
 * (with the bottleneck report), FAILED/TIMEOUT (with whatever detail the
 * backend returned). Never invents a success it didn't get. */
export function GeneratePanel({ schoolId, onGenerated }: GeneratePanelProps) {
  const [reason, setReason] = useState('')
  const generate = useGenerateSchedule(schoolId)

  function handleGenerate() {
    generate.mutate(
      { request_id: crypto.randomUUID(), reason: reason || undefined },
      { onSuccess: (result) => onGenerated(result.version?.id ?? null) },
    )
  }

  return (
    <section>
      <h3>Generate a schedule</h3>
      <label htmlFor="generate-reason">Reason (optional)</label>
      <input id="generate-reason" value={reason} onChange={(e) => setReason(e.target.value)} />
      <button type="button" onClick={handleGenerate} disabled={generate.isPending}>
        {generate.isPending ? 'Generating…' : 'Generate'}
      </button>

      {generate.data && (
        <div role="status">
          <p>Status: {generate.data.status}</p>
          {generate.data.status === 'VALID' && generate.data.version && (
            <p>
              Created draft version {generate.data.version.id} with{' '}
              {generate.data.version.assignment_count} assignments
              {generate.data.version.score && (
                <> — quality {generate.data.version.score.quality.toFixed(1)}/100</>
              )}
              .
            </p>
          )}
          {generate.data.status === 'INFEASIBLE' && generate.data.infeasibility && (
            <div>
              <p>{generate.data.infeasibility.note ?? 'No valid schedule could be found.'}</p>
              <ul>
                {generate.data.infeasibility.bottlenecks.map((b, i) => (
                  <li key={i}>
                    {b.subject_id}
                    {b.required_capability ? ` (needs ${b.required_capability})` : ''}: needs{' '}
                    {b.required}, only {b.available} available (short by {b.shortage}).
                  </li>
                ))}
              </ul>
            </div>
          )}
          {(generate.data.status === 'FAILED' || generate.data.status === 'TIMEOUT') && (
            <p>{generate.data.error ?? `Generation ended with status ${generate.data.status}.`}</p>
          )}
        </div>
      )}
      {generate.isError && <p role="alert">{(generate.error as Error).message}</p>}
    </section>
  )
}
