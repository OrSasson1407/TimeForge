import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query'
import { ApiError } from '../services/apiClient'
import { showToast } from '../state/toastStore'

const MAX_RETRIES = 2

/** A rejected request (validation failure, 403, 404...) won't succeed on
 * retry — only network-level failures and 5xx are worth retrying
 * ("Retry failed requests" UX, docs/02-PRD.md). */
function shouldRetry(failureCount: number, error: unknown): boolean {
  if (failureCount >= MAX_RETRIES) return false
  if (error instanceof ApiError) return error.status >= 500
  return true // TypeError from fetch itself — offline/DNS/connection reset
}

function retryDelay(attemptIndex: number): number {
  return Math.min(1000 * 2 ** attemptIndex, 8000)
}

function messageFor(error: unknown): string {
  if (!navigator.onLine) return "You're offline — check your connection and try again."
  if (error instanceof ApiError) return error.message
  if (error instanceof TypeError) return 'Network error — check your connection.'
  return 'Something went wrong.'
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: shouldRetry,
      retryDelay,
      staleTime: 10_000,
    },
    mutations: {
      // Mutations aren't auto-retried (docs/07-CODE_STANDARDS.md #9: many
      // are non-idempotent — approve/suspend/etc. — auto-retry on
      // ambiguous failure risks a duplicate side effect). The error toast
      // below is the retry surface: the user re-submits deliberately.
      retry: false,
    },
  },
  queryCache: new QueryCache({
    onError: (error, query) => {
      // Network-level failures are worth a global toast (the user may not
      // even be looking at the page that triggered the fetch). Rejected
      // requests (ApiError) are left to each page's own inline ErrorState
      // — a toast on top of an already-visible inline error is noise.
      if (error instanceof ApiError) return
      showToast({
        type: 'error',
        message: messageFor(error),
        action: {
          label: 'Retry',
          onClick: () => void queryClient.refetchQueries({ queryKey: query.queryKey }),
        },
      })
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      showToast({ type: 'error', message: messageFor(error) })
    },
  }),
})
