import { Navigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'

/** Shown instead of the app for a signed-in user whose backend User is
 * still `role: 'PENDING'` (docs/02-PRD.md #28a) — RequireAuth routes here
 * rather than letting a PENDING user see (and probe) the real app, since
 * the backend would refuse every request anyway. Sits outside RequireAuth
 * (which would otherwise redirect back here, looping), so it re-checks
 * signed-in-and-still-pending itself. */
export function PendingApprovalPage() {
  const { user, loading, signOut } = useAuth()

  if (loading) return <p>Loading…</p>
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'PENDING') return <Navigate to="/" replace />

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <span className="pending-badge">Pending approval</span>
        <h1>Almost there, {user.display_name.split(' ')[0]}</h1>
        <p className="auth-subtitle">
          Your email is verified. An administrator at your school still needs to review and approve
          your account before you can sign in to TimeForge.
        </p>
        <p className="field-hint">
          Check back later, or reach out to your school's administrator if this is taking longer
          than expected.
        </p>
        <button
          type="button"
          className="btn btn-secondary btn-block"
          onClick={() => void signOut()}
        >
          Sign out
        </button>
      </div>
    </main>
  )
}
