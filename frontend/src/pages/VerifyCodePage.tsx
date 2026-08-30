import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useResendCode, useVerifyCode } from '../hooks/useAuthFlow'
import { ApiError } from '../services/apiClient'

const RESEND_COOLDOWN_SECONDS = 60

export function VerifyCodePage() {
  const navigate = useNavigate()
  const location = useLocation()
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
      setError(err instanceof ApiError ? err.message : 'Verification failed.')
    }
  }

  async function handleResend() {
    setError(null)
    setResendMessage(null)
    try {
      await resendCode.mutateAsync(email)
      setResendMessage('A new code has been sent.')
      setCooldown(RESEND_COOLDOWN_SECONDS)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not resend the code.')
    }
  }

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <h1>Check your email</h1>
        <p className="auth-subtitle">
          We sent a 6-digit verification code to your email address. Enter it below to confirm your
          account.
        </p>

        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}
        {resendMessage && <div className="alert alert-success">{resendMessage}</div>}

        <form onSubmit={handleSubmit}>
          {!emailFromState && (
            <div className="field">
              <label htmlFor="verify-email">Email</label>
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
            <label htmlFor="verify-code">Verification code</label>
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
            {verifyCode.isPending ? 'Verifying…' : 'Verify email'}
          </button>
        </form>

        <p className="auth-switch">
          Didn&apos;t get a code?{' '}
          <button
            type="button"
            className="btn-link"
            onClick={() => void handleResend()}
            disabled={resendCode.isPending || cooldown > 0}
          >
            {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend code'}
          </button>
        </p>
        <p className="auth-switch">
          <Link to="/login">Back to sign in</Link>
        </p>
      </div>
    </main>
  )
}
