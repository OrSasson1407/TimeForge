import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PasswordStrengthMeter, passwordMeetsAllRules } from '../components/PasswordStrengthMeter'
import { Recaptcha } from '../components/Recaptcha'
import { useRegister, usePublicSchools } from '../hooks/useAuthFlow'
import { ApiError } from '../services/apiClient'
import { useLanguage } from '../state/LanguageContext'

const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY

export function RegisterPage() {
  const navigate = useNavigate()
  const { t } = useLanguage()
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
      setFormError(t('register.errorWeakPassword'))
      return
    }
    if (password !== confirmPassword) {
      setFormError(t('register.errorPasswordMismatch'))
      return
    }
    if (!schoolId) {
      setFormError(t('register.errorNoSchool'))
      return
    }
    if (!recaptchaToken) {
      setFormError(t('register.errorNoRecaptcha'))
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
      setFormError(err instanceof ApiError ? err.message : t('register.errorGeneric'))
    }
  }

  const submitting = register.isPending

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <h2>{t('register.title')}</h2>
        <p className="auth-subtitle">{t('register.subtitle')}</p>

        {formError && (
          <div className="alert alert-danger" role="alert">
            {formError}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="register-name">{t('register.fullName')}</label>
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
            <label htmlFor="register-email">{t('register.email')}</label>
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
            <label htmlFor="register-school">{t('register.school')}</label>
            <select
              id="register-school"
              value={schoolId}
              onChange={(e) => setSchoolId(e.target.value)}
              required
            >
              <option value="" disabled>
                {schools.isLoading ? t('register.loadingSchools') : t('register.selectSchool')}
              </option>
              {schools.data?.map((school) => (
                <option key={school.id} value={school.id}>
                  {school.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="register-password">{t('register.password')}</label>
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
            <label htmlFor="register-confirm-password">{t('register.confirmPassword')}</label>
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
            <p className="field-hint">{t('register.recaptchaSkipped')}</p>
          )}

          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? t('register.submitting') : t('register.submit')}
          </button>
        </form>

        <p className="auth-switch">
          {t('register.haveAccount')} <Link to="/login">{t('register.signIn')}</Link>
        </p>
      </div>
    </main>
  )
}
