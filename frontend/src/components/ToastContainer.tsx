import { useToasts } from '../hooks/useToasts'
import { dismissToast } from '../state/toastStore'
import type { Toast } from '../state/toastStore'

/** Renders the global toast stack (docs/02-PRD.md UX notes). Errors use
 * role="alert" (assertive — interrupts screen readers immediately);
 * success/info/warning use role="status" (polite — announced without
 * interrupting whatever the user is doing). */
export function ToastContainer() {
  const toasts = useToasts()

  if (toasts.length === 0) return null

  return (
    <div className="toast-stack" aria-label="Notifications">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  )
}

function ToastItem({ toast }: { toast: Toast }) {
  const isUrgent = toast.type === 'error' || toast.type === 'warning'

  return (
    <div
      className={`toast toast-${toast.type}`}
      role={isUrgent ? 'alert' : 'status'}
      aria-live={isUrgent ? 'assertive' : 'polite'}
    >
      <span className="toast-message">{toast.message}</span>
      {toast.action && (
        <button
          type="button"
          className="toast-action"
          onClick={() => {
            toast.action?.onClick()
            dismissToast(toast.id)
          }}
        >
          {toast.action.label}
        </button>
      )}
      <button
        type="button"
        className="toast-dismiss"
        aria-label="Dismiss notification"
        onClick={() => dismissToast(toast.id)}
      >
        ×
      </button>
    </div>
  )
}
