import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PasswordStrengthMeter, passwordMeetsAllRules } from '../components/PasswordStrengthMeter'
import { Recaptcha } from '../components/Recaptcha'
import { useRegister, usePublicSchools } from '../hooks/useAuthFlow'
import { ApiError } from '../services/apiClient'

const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY

export function RegisterPage() {
  const navigate = useNavigate()
  const schools = usePublicSchools()
  const register = useRegister()

  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [schoolId, setSchoolId] = useState('')
  // Dev fallback: no site key configured means the backend also has no
  // secret key and skips verification (see app/core/security.py's
  // verify_recaptcha) — any non-empty placeholder satisfies the request
  // schema in that case.
  const [recaptchaToken, setRecaptchaToken] = useState<string | null>(
    RECAPTCHA_SITE_KEY ? null : 'recaptcha-not-configured',
  )
  const [formError, setFormError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)

    if (!passwordMeetsAllRules(password)) {
      setFormError('Password does not meet the minimum strength requirements.')
      return
    }
    if (password !== confirmPassword) {
      setFormError('Passwords do not match.')
      return
    }
    if (!schoolId) {
      setFormError('Please select your school.')
      return
    }
    if (!recaptchaToken) {
      setFormError('Please complete the reCAPTCHA challenge.')
      return
    }

    try {
      await register.mutateAsync({
        email,
        password,
        display_name: displayName,
        school_id: schoolId,
        recaptcha_token: recaptchaToken,
      })
      navigate('/verify-email', { state: { email } })
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Registration failed.')
    }
  }

  const submitting = register.isPending

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <h1>Create your account</h1>
        <p className="auth-subtitle">
          Register, verify your email, and an administrator will approve your access.
        </p>

        {formError && (
          <div className="alert alert-danger" role="alert">
            {formError}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="register-name">Full name</label>
            <input
              id="register-name"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              autoComplete="name"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="register-email">Email</label>
            <input
              id="register-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="register-school">School</label>
            <select
              id="register-school"
              value={schoolId}
              onChange={(e) => setSchoolId(e.target.value)}
              required
            >
              <option value="" disabled>
                {schools.isLoading ? 'Loading schools…' : 'Select your school'}
              </option>
              {schools.data?.map((school) => (
                <option key={school.id} value={school.id}>
                  {school.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="register-password">Password</label>
            <input
              id="register-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
            <PasswordStrengthMeter password={password} />
          </div>

          <div className="field">
            <label htmlFor="register-confirm-password">Confirm password</label>
            <input
              id="register-confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
          </div>

          {RECAPTCHA_SITE_KEY ? (
            <div className="field">
              <Recaptcha siteKey={RECAPTCHA_SITE_KEY} onChange={setRecaptchaToken} />
            </div>
          ) : (
            <p className="field-hint">
              reCAPTCHA isn't configured for this environment — skipping the challenge.
            </p>
          )}

          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </main>
  )
}
