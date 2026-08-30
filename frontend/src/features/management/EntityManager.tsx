/**
 * One generic admin CRUD screen (list + create/edit form), parametrized per
 * entity — the frontend counterpart of the backend's generic
 * `build_crud_router` (backend/app/api/crud_router.py): built once, reused
 * for all seven catalog entities, rather than seven near-identical screens.
 *
 * Form state is kept as `Record<string, string>` regardless of the
 * underlying field's real type (number/boolean/list) — `toUpsert` converts
 * it to the real `TUpsert` shape on submit, `toFormState` converts an
 * existing entity back for editing. This keeps the generic renderer simple
 * (it only ever deals with string inputs) while each entity's config still
 * owns its own real types.
 *
 * Labels/titles/help text are translation keys, not literal strings —
 * `entityConfigs.ts` stays a static, English-free config; this component is
 * the one place that resolves them via `t()`, the same split DataTable uses
 * between "generic renderer" and "i18n-aware caller".
 */
import { useState } from 'react'
import type { FormEvent } from 'react'
import { DataTable } from '../../components/DataTable'
import type { DataTableColumn } from '../../components/DataTable'
import { useLanguage } from '../../state/LanguageContext'
import type { TranslationKey } from '../../i18n/translations'

export interface FieldSpec {
  key: string
  labelKey: TranslationKey
  input: 'text' | 'number' | 'checkbox' | 'select'
  options?: string[]
  helpTextKey?: TranslationKey
}

export interface EntityColumnSpec<TEntity> {
  key: string
  labelKey: TranslationKey
  render: (row: TEntity) => string
}

export interface EntityManagerConfig<TEntity extends { id: string }, TUpsert> {
  titleKey: TranslationKey
  fields: FieldSpec[]
  columns: EntityColumnSpec<TEntity>[]
  toFormState: (entity: TEntity) => Record<string, string>
  emptyFormState: Record<string, string>
  toUpsert: (form: Record<string, string>) => TUpsert
}

interface EntityManagerProps<TEntity extends { id: string }, TUpsert> {
  config: EntityManagerConfig<TEntity, TUpsert>
  entities: TEntity[]
  isSaving: boolean
  saveError: string | null
  onSave: (id: string, body: TUpsert) => void
}

export function EntityManager<TEntity extends { id: string }, TUpsert>({
  config,
  entities,
  isSaving,
  saveError,
  onSave,
}: EntityManagerProps<TEntity, TUpsert>) {
  const { t } = useLanguage()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<Record<string, string>>({ id: '', ...config.emptyFormState })

  function startNew() {
    setEditingId(null)
    setForm({ id: '', ...config.emptyFormState })
  }

  function startEdit(entity: TEntity) {
    setEditingId(entity.id)
    setForm({ id: entity.id, ...config.toFormState(entity) })
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!form.id) return
    onSave(form.id, config.toUpsert(form))
  }

  const title = t(config.titleKey)
  const columns: DataTableColumn<TEntity>[] = config.columns.map((column) => ({
    key: column.key,
    label: t(column.labelKey),
    render: column.render,
  }))

  return (
    <section>
      <h2>{title}</h2>
      <DataTable rows={entities} columns={columns} getRowId={(row) => row.id} onEdit={startEdit} />

      <form
        onSubmit={handleSubmit}
        aria-label={
          editingId
            ? t('entityManager.editAriaLabel', { title })
            : t('entityManager.newAriaLabel', { title })
        }
      >
        <h3>
          {editingId
            ? t('entityManager.editingHeading', { id: editingId })
            : t('entityManager.new')}
        </h3>
        <div>
          <label htmlFor="entity-id">{t('entityManager.id')}</label>
          <input
            id="entity-id"
            value={form.id}
            disabled={editingId !== null}
            onChange={(e) => setForm({ ...form, id: e.target.value })}
            required
          />
        </div>
        {config.fields.map((field) => (
          <div key={field.key}>
            <label htmlFor={`entity-field-${field.key}`}>{t(field.labelKey)}</label>
            {field.input === 'select' ? (
              <select
                id={`entity-field-${field.key}`}
                value={form[field.key] ?? ''}
                onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
              >
                {(field.options ?? []).map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            ) : field.input === 'checkbox' ? (
              <input
                id={`entity-field-${field.key}`}
                type="checkbox"
                checked={form[field.key] === 'true'}
                onChange={(e) =>
                  setForm({ ...form, [field.key]: e.target.checked ? 'true' : 'false' })
                }
              />
            ) : (
              <input
                id={`entity-field-${field.key}`}
                type={field.input === 'number' ? 'number' : 'text'}
                value={form[field.key] ?? ''}
                onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
              />
            )}
            {field.helpTextKey && <p>{t(field.helpTextKey)}</p>}
          </div>
        ))}
        <button type="submit" disabled={isSaving}>
          {isSaving ? t('entityManager.saving') : t('entityManager.save')}
        </button>
        {editingId && (
          <button type="button" onClick={startNew}>
            {t('entityManager.cancel')}
          </button>
        )}
        {saveError && <p role="alert">{saveError}</p>}
      </form>
    </section>
  )
}
