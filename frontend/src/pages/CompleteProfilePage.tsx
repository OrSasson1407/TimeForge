import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useCompleteOAuthProfile, usePublicSchools } from '../hooks/useAuthFlow'
import { ApiError } from '../services/apiClient'
import { useLanguage } from '../state/LanguageContext'

/** Shown after a first-time Google sign-in (docs/02-PRD.md #28a): Firebase
 * already has a verified identity, but TimeForge doesn't have a User
 * record yet. Collects the one thing Google doesn't know — which school —
 * then the account lands PENDING, same as email/password registration. */
export function CompleteProfilePage() {
  const { needsOnboarding, oauthProfile, loading, refreshUser } = useAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const schools = usePublicSchools()
  const completeProfile = useCompleteOAuthProfile()

  const [displayName, setDisplayName] = useState(oauthProfile?.displayName ?? '')
  const [schoolId, setSchoolId] = useState('')
  const [error, setError] = useState<string | null>(null)

  if (loading) return <p>{t('common.loading')}</p>
  if (!needsOnboarding) return <Navigate to="/" replace />

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!schoolId) {
      setError(t('profile.errorNoSchool'))
      return
    }
    try {
      await completeProfile.mutateAsync({ display_name: displayName, school_id: schoolId })
      await refreshUser()
      navigate('/')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('profile.errorGeneric'))
    }
  }

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <h2>{t('profile.title')}</h2>
        <p className="auth-subtitle">
          {t('profile.subtitle', { email: oauthProfile?.email ?? t('profile.yourGoogleAccount') })}
        </p>

        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="profile-name">{t('profile.fullName')}</label>
            <input
              id="profile-name"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="profile-school">{t('profile.school')}</label>
            <select
              id="profile-school"
              value={schoolId}
              onChange={(e) => setSchoolId(e.target.value)}
              required
            >
              <option value="" disabled>
                {schools.isLoading ? t('profile.loadingSchools') : t('profile.selectSchool')}
              </option>
              {schools.data?.map((school) => (
                <option key={school.id} value={school.id}>
                  {school.name}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={completeProfile.isPending}
          >
            {completeProfile.isPending ? t('profile.submitting') : t('profile.submit')}
          </button>
        </form>
      </div>
    </main>
  )
}
