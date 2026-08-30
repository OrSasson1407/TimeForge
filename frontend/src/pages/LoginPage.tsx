import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'

export function LoginPage() {
  const { signIn, signInWithGoogle, error } = useAuth()
  const { t } = useLanguage()
  const location = useLocation()
  const navigate = useNavigate()
  const verifiedNotice = (location.state as { verified?: boolean } | null)?.verified
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [googleSubmitting, setGoogleSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    try {
      await signIn(email, password)
      // `user` itself resolves a moment later (AuthContext's onAuthStateChanged
      // -> /auth/me is async); RequireAuth/RequireAdmin sort out the actual
      // destination (dashboard, or /pending-approval for a PENDING account)
      // once it does, showing its own "Loading…" state in the meantime.
      navigate('/')
    } catch {
      // `error` from context already carries the user-facing message.
    } finally {
      setSubmitting(false)
    }
  }

  async function handleGoogleSignIn() {
    setGoogleSubmitting(true)
    try {
      await signInWithGoogle()
      // First-time Google identities land on /complete-profile instead of
      // "/" via RequireAuth's needsOnboarding check — navigating to "/" is
      // still correct either way.
      navigate('/')
    } catch {
      // `error` from context already carries the user-facing message.
    } finally {
      setGoogleSubmitting(false)
    }
  }

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <h2>{t('login.title')}</h2>
        <p className="auth-subtitle">{t('login.subtitle')}</p>

        {verifiedNotice && <div className="alert alert-success">{t('login.verifiedNotice')}</div>}
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="login-email">{t('login.email')}</label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="login-password">{t('login.password')}</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <p className="field-hint" style={{ textAlign: 'end', marginBottom: '1em' }}>
            <Link to="/forgot-password">{t('login.forgotPassword')}</Link>
          </p>
          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? t('login.submitting') : t('login.submit')}
          </button>
        </form>

        <div
          role="separator"
          aria-label={t('login.or')}
          style={{
            textAlign: 'center',
            margin: '1.25em 0',
            color: 'var(--color-text-muted)',
            fontSize: '0.8rem',
          }}
        >
          {t('login.or')}
        </div>

        <button
          type="button"
          className="btn btn-secondary btn-block"
          onClick={() => void handleGoogleSignIn()}
          disabled={googleSubmitting}
        >
          {googleSubmitting ? t('login.googleConnecting') : t('login.google')}
        </button>

        <p className="auth-switch">
          {t('login.noAccount')} <Link to="/register">{t('login.createOne')}</Link>
        </p>
      </div>
    </main>
  )
}
