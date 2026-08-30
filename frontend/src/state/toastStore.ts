/**
 * Toast/notification store (docs/01-CLAUDE.md rule 11: state separated by
 * concern). A plain module-level pub-sub rather than a React Context —
 * `queryClient.ts` needs to push toasts from outside the component tree
 * (query/mutation error handlers run in TanStack Query's cache, not in a
 * component), so the store has to exist independent of React. Components
 * read it via `useSyncExternalStore` (see hooks/useToasts.ts).
 */
export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface Toast {
  id: string
  type: ToastType
  message: string
  action?: { label: string; onClick: () => void }
}

type Listener = () => void

let toasts: Toast[] = []
const listeners = new Set<Listener>()

function emit() {
  for (const listener of listeners) listener()
}

export function getToasts(): Toast[] {
  return toasts
}

export function subscribeToasts(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

const DEFAULT_DURATION_MS = 6000

export function showToast(toast: Omit<Toast, 'id'>, durationMs = DEFAULT_DURATION_MS): string {
  const id = crypto.randomUUID()
  toasts = [...toasts, { ...toast, id }]
  emit()
  if (durationMs > 0) {
    setTimeout(() => dismissToast(id), durationMs)
  }
  return id
}

export function dismissToast(id: string): void {
  toasts = toasts.filter((toast) => toast.id !== id)
  emit()
}
