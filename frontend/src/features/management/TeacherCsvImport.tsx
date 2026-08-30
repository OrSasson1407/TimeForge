import { useRef, useState } from 'react'
import { parseCsvWithHeader } from '../../lib/csv'
import { showToast } from '../../state/toastStore'
import { useLanguage } from '../../state/LanguageContext'
import type { TranslationKey } from '../../i18n/translations'
import type { TeacherUpsertRequest } from '../../types/catalog'

interface ParsedRow {
  id: string
  body: TeacherUpsertRequest
  error: string | null
}

/** Expected columns: id, name, email, subject_ids (semicolon-separated —
 * commas are already the CSV delimiter), max_weekly_load, max_consecutive. */
function toRow(record: Record<string, string>, t: (key: TranslationKey) => string): ParsedRow {
  const id = record.id?.trim() ?? ''
  const name = record.name?.trim() ?? ''
  const email = record.email?.trim() ?? ''
  const subjectIds = (record.subject_ids ?? '')
    .split(';')
    .map((s) => s.trim())
    .filter(Boolean)
  const maxWeeklyLoad = Number(record.max_weekly_load)
  const maxConsecutive = Number(record.max_consecutive)

  const problems: string[] = []
  if (!id) problems.push(t('csvImport.missingId'))
  if (!name) problems.push(t('csvImport.missingName'))
  if (!email) problems.push(t('csvImport.missingEmail'))
  if (!Number.isFinite(maxWeeklyLoad) || maxWeeklyLoad <= 0)
    problems.push(t('csvImport.invalidMaxWeeklyLoad'))
  if (!Number.isFinite(maxConsecutive) || maxConsecutive <= 0)
    problems.push(t('csvImport.invalidMaxConsecutive'))

  return {
    id,
    body: {
      name,
      email,
      subject_ids: subjectIds,
      max_weekly_load: Number.isFinite(maxWeeklyLoad) ? maxWeeklyLoad : 0,
      max_consecutive: Number.isFinite(maxConsecutive) ? maxConsecutive : 0,
    },
    error: problems.length > 0 ? problems.join(', ') : null,
  }
}

export function TeacherCsvImport({
  onImport,
}: {
  /** Upserts one teacher; rejects on failure. The caller owns the actual
   * mutation (teacherHooks.useUpsert) so this component stays generic
   * about how a row gets persisted. */
  onImport: (id: string, body: TeacherUpsertRequest) => Promise<unknown>
}) {
  const { t } = useLanguage()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [rows, setRows] = useState<ParsedRow[] | null>(null)
  const [importing, setImporting] = useState(false)
  const [open, setOpen] = useState(false)

  function handleFile(file: File) {
    const reader = new FileReader()
    reader.onload = () => {
      const text = typeof reader.result === 'string' ? reader.result : ''
      const parsed = parseCsvWithHeader(text).map((record) => toRow(record, t))
      setRows(parsed)
    }
    reader.readAsText(file)
  }

  async function handleImport() {
    if (!rows) return
    const valid = rows.filter((r) => !r.error)
    setImporting(true)
    let succeeded = 0
    let failed = 0
    for (const row of valid) {
      try {
        await onImport(row.id, row.body)
        succeeded++
      } catch {
        failed++
      }
    }
    setImporting(false)
    setRows(null)
    setOpen(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
    showToast({
      type: failed > 0 ? 'error' : 'success',
      message:
        failed > 0
          ? t('csvImport.resultPartial', { count: succeeded, failed })
          : t('csvImport.resultSuccess', { count: succeeded }),
    })
  }

  if (!open) {
    return (
      <button type="button" className="btn btn-secondary" onClick={() => setOpen(true)}>
        {t('csvImport.button')}
      </button>
    )
  }

  const validCount = rows?.filter((r) => !r.error).length ?? 0
  const errorCount = rows ? rows.length - validCount : 0

  return (
    <div className="auth-card" style={{ maxWidth: 640, margin: '1rem 0' }}>
      <h3 style={{ marginTop: 0 }}>{t('csvImport.title')}</h3>
      <p className="field-hint">{t('csvImport.help')}</p>
      <div className="field">
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv"
          aria-label={t('csvImport.fileLabel')}
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
          }}
        />
      </div>

      {rows && (
        <>
          <p>
            {t('csvImport.rowsReady', { count: validCount })}
            {errorCount > 0 ? t('csvImport.rowsWithErrors', { count: errorCount }) : ''}.
          </p>
          <div
            style={{ maxHeight: 260, overflow: 'auto', border: '1px solid var(--color-border)' }}
          >
            <table>
              <thead>
                <tr>
                  <th>{t('csvImport.columnId')}</th>
                  <th>{t('csvImport.columnName')}</th>
                  <th>{t('csvImport.columnEmail')}</th>
                  <th>{t('csvImport.columnStatus')}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={`${row.id}-${i}`}>
                    <td>{row.id || '—'}</td>
                    <td>{row.body.name || '—'}</td>
                    <td>{row.body.email || '—'}</td>
                    <td style={row.error ? { color: 'var(--color-danger)' } : undefined}>
                      {row.error ?? t('csvImport.ok')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => void handleImport()}
          disabled={!rows || validCount === 0 || importing}
        >
          {importing
            ? t('csvImport.importing')
            : t('csvImport.importButton', { count: validCount || '' })}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => {
            setOpen(false)
            setRows(null)
            if (fileInputRef.current) fileInputRef.current.value = ''
          }}
          disabled={importing}
        >
          {t('csvImport.cancel')}
        </button>
      </div>
    </div>
  )
}
