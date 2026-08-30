import { useEffect, useState } from 'react'
import { apiClient } from '../services/apiClient'
import type { HealthStatus } from '../types/health'

type ApiStatus = 'checking' | 'online' | 'offline'

/** A small persistent indicator of backend reachability — extracted out of
 * the old top-level App component so it can live in the shared header and
 * be shown on every page, including the (unauthenticated) login page. */
export function BackendStatusBadge() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')

  useEffect(() => {
    let cancelled = false

    apiClient
      .get<HealthStatus>('/health')
      .then(() => {
        if (!cancelled) setApiStatus('online')
      })
      .catch(() => {
        if (!cancelled) setApiStatus('offline')
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <span>
      Backend API: <span data-testid="api-status">{apiStatus}</span>
    </span>
  )
}
