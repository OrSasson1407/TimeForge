import { useEffect, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'
import { useSchedulingConfig, useUpdateSchedulingConfig } from '../hooks/useSchedulingConfig'
import type { SchedulingConfig } from '../types/schedulingConfig'

export function ConstraintsPage() {
  const { user } = useAuth()
  const { t } = useLanguage()
  const schoolId = user?.school_id
  const { data: config } = useSchedulingConfig(schoolId)
  const update = useUpdateSchedulingConfig(schoolId)

  const [draft, setDraft] = useState<SchedulingConfig | null>(null)

  useEffect(() => {
    if (config) setDraft(config)
  }, [config])

  if (!draft) return <p>{t('availability.loading')}</p>

  function setWeight(constraintId: string, value: number) {
    setDraft((prev) =>
      prev
        ? {
            ...prev,
            soft_constraint_weights: { ...prev.soft_constraint_weights, [constraintId]: value },
          }
        : prev,
    )
  }

  return (
    <main>
      <h2>{t('constraints.title')}</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          update.mutate(draft)
        }}
      >
        <fieldset>
          <legend>{t('constraints.softWeights')}</legend>
          {Object.entries(draft.soft_constraint_weights)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([constraintId, weight]) => (
              <div key={constraintId}>
                <label htmlFor={`weight-${constraintId}`}>{constraintId}</label>
                <input
                  id={`weight-${constraintId}`}
                  type="number"
                  step="0.1"
                  min="0"
                  value={weight}
                  onChange={(e) => setWeight(constraintId, Number(e.target.value))}
                />
              </div>
            ))}
        </fieldset>

        <fieldset>
          <legend>{t('constraints.solverParams')}</legend>
          <div>
            <label htmlFor="config-timeout">{t('constraints.timeoutSeconds')}</label>
            <input
              id="config-timeout"
              type="number"
              min="1"
              value={draft.timeout_seconds}
              onChange={(e) => setDraft({ ...draft, timeout_seconds: Number(e.target.value) })}
            />
          </div>
          <div>
            <label htmlFor="config-seed">{t('constraints.randomSeed')}</label>
            <input
              id="config-seed"
              type="number"
              value={draft.random_seed}
              onChange={(e) => setDraft({ ...draft, random_seed: Number(e.target.value) })}
            />
          </div>
          <div>
            <label htmlFor="config-quality-decay">{t('constraints.qualityDecay')}</label>
            <input
              id="config-quality-decay"
              type="number"
              step="0.01"
              min="0.001"
              value={draft.quality_decay_k}
              onChange={(e) => setDraft({ ...draft, quality_decay_k: Number(e.target.value) })}
            />
          </div>
        </fieldset>

        <button type="submit" disabled={update.isPending}>
          {update.isPending ? t('constraints.saving') : t('constraints.save')}
        </button>
        {update.isError && <p role="alert">{(update.error as Error).message}</p>}
        {update.isSuccess && <p>{t('constraints.saved')}</p>}
      </form>
    </main>
  )
}
