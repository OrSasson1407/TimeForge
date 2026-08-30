import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'

export function LoginPage() {
  const { signIn, signInWithGoogle, error } = useAuth()
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
        <h1>Welcome back</h1>
        <p className="auth-subtitle">Sign in to your TimeForge account.</p>

        {verifiedNotice && (
          <div className="alert alert-success">
            Email verified. Your account is awaiting administrator approval — you can sign in in the
            meantime.
          </div>
        )}
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="login-email">Email</label>
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
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <p className="field-hint" style={{ textAlign: 'right', marginBottom: '1em' }}>
            <Link to="/forgot-password">Forgot password?</Link>
          </p>
          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div
          role="separator"
          aria-label="or"
          style={{
            textAlign: 'center',
            margin: '1.25em 0',
            color: 'var(--color-text-muted)',
            fontSize: '0.8rem',
          }}
        >
          or
        </div>

        <button
          type="button"
          className="btn btn-secondary btn-block"
          onClick={() => void handleGoogleSignIn()}
          disabled={googleSubmitting}
        >
          {googleSubmitting ? 'Connecting…' : 'Continue with Google'}
        </button>

        <p className="auth-switch">
          Don&apos;t have an account? <Link to="/register">Create one</Link>
        </p>
      </div>
    </main>
  )
}
