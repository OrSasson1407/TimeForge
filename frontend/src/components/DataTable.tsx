import { useEffect, useMemo, useState } from 'react'
import { useLanguage } from '../state/LanguageContext'

export interface DataTableColumn<T> {
  key: string
  label: string
  render: (row: T) => string
}

interface DataTableProps<T> {
  rows: T[]
  columns: DataTableColumn<T>[]
  getRowId: (row: T) => string
  onEdit?: (row: T) => void
  emptyMessage?: string
  /** Client-side search across every column's rendered text — fine for the
   * catalog-sized lists this reuses across (dozens, not thousands, of
   * rows); a genuinely large table (e.g. a school with years of audit
   * history) would need server-side search instead. */
  searchable?: boolean
  searchPlaceholder?: string
  pageSize?: number
}

const DEFAULT_PAGE_SIZE = 10

/** A small, presentational table (docs/07-CODE_STANDARDS.md #9: data-fetching
 * lives in hooks/, not here) reused across every management screen. */
export function DataTable<T>({
  rows,
  columns,
  getRowId,
  onEdit,
  emptyMessage,
  searchable = true,
  searchPlaceholder,
  pageSize = DEFAULT_PAGE_SIZE,
}: DataTableProps<T>) {
  const { t } = useLanguage()
  const resolvedEmptyMessage = emptyMessage ?? t('dataTable.noRecords')
  const resolvedSearchPlaceholder = searchPlaceholder ?? t('dataTable.search')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(0)

  const filtered = useMemo(() => {
    if (!query.trim()) return rows
    const needle = query.trim().toLowerCase()
    return rows.filter((row) =>
      columns.some((column) => column.render(row).toLowerCase().includes(needle)),
    )
  }, [rows, columns, query])

  const pageCount = Math.max(Math.ceil(filtered.length / pageSize), 1)
  const clampedPage = Math.min(page, pageCount - 1)
  const pageRows = filtered.slice(clampedPage * pageSize, clampedPage * pageSize + pageSize)

  // Reset to page 0 whenever the filtered set changes shape (new search,
  // or the underlying data shrank below the current page).
  useEffect(() => {
    setPage(0)
  }, [query])

  if (rows.length === 0) {
    return <p>{resolvedEmptyMessage}</p>
  }

  return (
    <div>
      {searchable && rows.length > pageSize && (
        <div className="field" style={{ maxWidth: 320 }}>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={resolvedSearchPlaceholder}
            aria-label={resolvedSearchPlaceholder}
          />
        </div>
      )}

      {filtered.length === 0 ? (
        <p>{t('dataTable.noMatches', { query })}</p>
      ) : (
        <>
          <table>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key}>{column.label}</th>
                ))}
                {onEdit && <th></th>}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row) => (
                <tr key={getRowId(row)}>
                  {columns.map((column) => (
                    <td key={column.key}>{column.render(row)}</td>
                  ))}
                  {onEdit && (
                    <td>
                      <button type="button" onClick={() => onEdit(row)}>
                        {t('dataTable.edit')}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>

          {pageCount > 1 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75em',
                marginTop: '0.75em',
                fontSize: '0.85rem',
              }}
            >
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setPage((p) => Math.max(p - 1, 0))}
                disabled={clampedPage === 0}
              >
                {t('dataTable.previous')}
              </button>
              <span className="field-hint">
                {t('dataTable.pageOf', {
                  page: clampedPage + 1,
                  total: pageCount,
                  count: filtered.length,
                })}
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setPage((p) => Math.min(p + 1, pageCount - 1))}
                disabled={clampedPage >= pageCount - 1}
              >
                {t('dataTable.next')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
