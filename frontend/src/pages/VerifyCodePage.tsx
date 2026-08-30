import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useResendCode, useVerifyCode } from '../hooks/useAuthFlow'
import { ApiError } from '../services/apiClient'
import { useLanguage } from '../state/LanguageContext'

const RESEND_COOLDOWN_SECONDS = 60

export function VerifyCodePage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useLanguage()
  const emailFromState = (location.state as { email?: string } | null)?.email

  const [email, setEmail] = useState(emailFromState ?? '')
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [resendMessage, setResendMessage] = useState<string | null>(null)
  const [cooldown, setCooldown] = useState(0)

  const verifyCode = useVerifyCode()
  const resendCode = useResendCode()

  useEffect(() => {
    if (cooldown <= 0) return
    const timer = setInterval(() => setCooldown((s) => Math.max(s - 1, 0)), 1000)
    return () => clearInterval(timer)
  }, [cooldown])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await verifyCode.mutateAsync({ email, code })
      navigate('/login', { state: { verified: true } })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('verify.errorGeneric'))
    }
  }

  async function handleResend() {
    setError(null)
    setResendMessage(null)
    try {
      await resendCode.mutateAsync(email)
      setResendMessage(t('verify.resendSuccess'))
      setCooldown(RESEND_COOLDOWN_SECONDS)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('verify.errorResend'))
    }
  }

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <h2>{t('verify.title')}</h2>
        <p className="auth-subtitle">{t('verify.subtitle')}</p>

        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}
        {resendMessage && <div className="alert alert-success">{resendMessage}</div>}

        <form onSubmit={handleSubmit}>
          {!emailFromState && (
            <div className="field">
              <label htmlFor="verify-email">{t('verify.email')}</label>
              <input
                id="verify-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          )}

          <div className="field">
            <label htmlFor="verify-code">{t('verify.code')}</label>
            <input
              id="verify-code"
              className="code-input"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={verifyCode.isPending}
          >
            {verifyCode.isPending ? t('verify.submitting') : t('verify.submit')}
          </button>
        </form>

        <p className="auth-switch">
          {t('verify.noCode')}{' '}
          <button
            type="button"
            className="btn-link"
            onClick={() => void handleResend()}
            disabled={resendCode.isPending || cooldown > 0}
          >
            {cooldown > 0 ? t('verify.resendIn', { seconds: cooldown }) : t('verify.resend')}
          </button>
        </p>
        <p className="auth-switch">
          <Link to="/login">{t('verify.backToSignIn')}</Link>
        </p>
      </div>
    </main>
  )
}
