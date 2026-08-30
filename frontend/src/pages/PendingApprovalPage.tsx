import { Navigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'

/** Shown instead of the app for a signed-in user whose backend User is
 * still `role: 'PENDING'` (docs/02-PRD.md #28a) — RequireAuth routes here
 * rather than letting a PENDING user see (and probe) the real app, since
 * the backend would refuse every request anyway. Sits outside RequireAuth
 * (which would otherwise redirect back here, looping), so it re-checks
 * signed-in-and-still-pending itself. */
export function PendingApprovalPage() {
  const { user, loading, signOut } = useAuth()
  const { t } = useLanguage()

  if (loading) return <p>{t('common.loading')}</p>
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'PENDING') return <Navigate to="/" replace />

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <span className="pending-badge">{t('pending.badge')}</span>
        <h2>{t('pending.title', { name: user.display_name.split(' ')[0] })}</h2>
        <p className="auth-subtitle">{t('pending.subtitle')}</p>
        <p className="field-hint">{t('pending.hint')}</p>
        <button
          type="button"
          className="btn btn-secondary btn-block"
          onClick={() => void signOut()}
        >
          {t('pending.signOut')}
        </button>
      </div>
    </main>
  )
}
