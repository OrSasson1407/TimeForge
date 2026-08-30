/**
 * Shared building blocks for the "Default → Loading → Empty → Error →
 * Success" state sequence every data-fetching feature goes through
 * (docs/02-PRD.md UX notes). TanStack Query already gives each page the
 * booleans (isLoading/isError/data) — these components are what render
 * each state consistently, instead of every page inventing its own
 * spinner/empty-message/error-banner.
 */

export function Spinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <span className="spinner" role="status" aria-label={label}>
      <span className="spinner-circle" aria-hidden="true" />
    </span>
  )
}

export function Skeleton({ width, height = '1em' }: { width?: string; height?: string }) {
  return <span className="skeleton" style={{ width: width ?? '100%', height }} aria-hidden="true" />
}

/** A skeleton shaped like a DataTable — same row/column count as the real
 * table so the layout doesn't jump once data arrives. */
export function SkeletonTable({ rows = 4, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <table aria-hidden="true">
      <tbody>
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <tr key={rowIndex}>
            {Array.from({ length: columns }).map((_, colIndex) => (
              <td key={colIndex}>
                <Skeleton />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export function EmptyState({
  title,
  message,
  action,
}: {
  title: string
  message?: string
  action?: { label: string; onClick: () => void }
}) {
  return (
    <div className="empty-state">
      <p className="empty-state-title">{title}</p>
      {message && <p className="field-hint">{message}</p>}
      {action && (
        <button type="button" className="btn btn-secondary" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  )
}

export function ErrorState({
  message = 'Something went wrong.',
  onRetry,
}: {
  message?: string
  onRetry?: () => void
}) {
  return (
    <div className="alert alert-danger" role="alert">
      <span>{message}</span>
      {onRetry && (
        <button
          type="button"
          className="btn-link"
          onClick={onRetry}
          style={{ marginLeft: '0.75em' }}
        >
          Retry
        </button>
      )}
    </div>
  )
}
