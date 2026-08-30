import { useState } from 'react'
import { useGenerateSchedule } from '../../hooks/useSchedule'
import { useLanguage } from '../../state/LanguageContext'

interface GeneratePanelProps {
  schoolId: string
  onGenerated: (versionId: string | null) => void
}

/** FR-009/FR-010/FR-011/FR-025: triggers generation and surfaces the
 * solver's outcome plainly — VALID (with the new version id), INFEASIBLE
 * (with the bottleneck report), FAILED/TIMEOUT (with whatever detail the
 * backend returned). Never invents a success it didn't get. */
export function GeneratePanel({ schoolId, onGenerated }: GeneratePanelProps) {
  const { t } = useLanguage()
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
      <h3>{t('generate.title')}</h3>
      <label htmlFor="generate-reason">{t('generate.reason')}</label>
      <input id="generate-reason" value={reason} onChange={(e) => setReason(e.target.value)} />
      <button type="button" onClick={handleGenerate} disabled={generate.isPending}>
        {generate.isPending ? t('generate.submitting') : t('generate.submit')}
      </button>

      {generate.data && (
        <div role="status">
          <p>{t('generate.status', { status: generate.data.status })}</p>
          {generate.data.status === 'VALID' && generate.data.version && (
            <p>
              {t('generate.createdDraft', {
                id: generate.data.version.id,
                count: generate.data.version.assignment_count,
              })}
              {generate.data.version.score && (
                <>
                  {t('generate.qualitySuffix', {
                    quality: generate.data.version.score.quality.toFixed(1),
                  })}
                </>
              )}
              .
            </p>
          )}
          {generate.data.status === 'INFEASIBLE' && generate.data.infeasibility && (
            <div>
              <p>{generate.data.infeasibility.note ?? t('generate.infeasibleDefault')}</p>
              <ul>
                {generate.data.infeasibility.bottlenecks.map((b, i) => (
                  <li key={i}>
                    {t('generate.bottleneckLine', {
                      subject: b.subject_id,
                      capability: b.required_capability
                        ? t('generate.bottleneckCapability', { capability: b.required_capability })
                        : '',
                      required: b.required,
                      available: b.available,
                      shortage: b.shortage,
                    })}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {(generate.data.status === 'FAILED' || generate.data.status === 'TIMEOUT') && (
            <p>
              {generate.data.error ??
                t('generate.endedWithStatus', { status: generate.data.status })}
            </p>
          )}
        </div>
      )}
      {generate.isError && <p role="alert">{(generate.error as Error).message}</p>}
    </section>
  )
}
