import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'

export function ForgotPasswordPage() {
  const { sendPasswordReset } = useAuth()
  const { t } = useLanguage()
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await sendPasswordReset(email)
      // Always show success, whether or not the email exists — otherwise
      // this becomes an account-enumeration oracle (docs/02-PRD.md #30
      // "never leak more detail than the caller needs").
      setSent(true)
    } catch {
      setSent(true)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <h2>{t('forgot.title')}</h2>
        <p className="auth-subtitle">{t('forgot.subtitle')}</p>

        {sent ? (
          <div className="alert alert-success">{t('forgot.sentNotice')}</div>
        ) : (
          <form onSubmit={handleSubmit}>
            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}
            <div className="field">
              <label htmlFor="forgot-email">{t('forgot.email')}</label>
              <input
                id="forgot-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
            <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? t('forgot.submitting') : t('forgot.submit')}
            </button>
          </form>
        )}

        <p className="auth-switch">
          <Link to="/login">{t('forgot.backToSignIn')}</Link>
        </p>
      </div>
    </main>
  )
}
