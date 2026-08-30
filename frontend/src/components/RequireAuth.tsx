import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'

/** Gate for every non-public route: redirects to /login when there is no
 * resolved backend User, and to /pending-approval for a PENDING one — the
 * backend refuses every real request from a PENDING user anyway, so there's
 * nothing for them to usefully see behind this gate (docs/02-PRD.md #28a).
 * Loading state is shown, never a flash of protected content, while the
 * auth check is in flight. */
export function RequireAuth() {
  const { user, loading, needsOnboarding } = useAuth()

  if (loading) return <p>Loading…</p>
  if (needsOnboarding) return <Navigate to="/complete-profile" replace />
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'PENDING') return <Navigate to="/pending-approval" replace />
  return <Outlet />
}

/** Gate for admin-only routes (docs/02-PRD.md §28 Permissions) — a signed-in
 * Teacher is redirected to the dashboard rather than shown a 403 page,
 * since the backend already refuses the underlying requests either way. */
export function RequireAdmin() {
  const { user, loading } = useAuth()

  if (loading) return <p>Loading…</p>
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'ADMIN') return <Navigate to="/" replace />
  return <Outlet />
}
