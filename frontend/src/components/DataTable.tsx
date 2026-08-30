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
}

/** A small, presentational table (docs/07-CODE_STANDARDS.md #9: data-fetching
 * lives in hooks/, not here) reused across every management screen. */
export function DataTable<T>({
  rows,
  columns,
  getRowId,
  onEdit,
  emptyMessage = 'No records yet.',
}: DataTableProps<T>) {
  if (rows.length === 0) {
    return <p>{emptyMessage}</p>
  }

  return (
    <table>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key}>{column.label}</th>
          ))}
          {onEdit && <th>Actions</th>}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={getRowId(row)}>
            {columns.map((column) => (
              <td key={column.key}>{column.render(row)}</td>
            ))}
            {onEdit && (
              <td>
                <button type="button" onClick={() => onEdit(row)}>
                  Edit
                </button>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
