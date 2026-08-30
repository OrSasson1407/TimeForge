import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useCompleteOAuthProfile, usePublicSchools } from '../hooks/useAuthFlow'
import { ApiError } from '../services/apiClient'

/** Shown after a first-time Google sign-in (docs/02-PRD.md #28a): Firebase
 * already has a verified identity, but TimeForge doesn't have a User
 * record yet. Collects the one thing Google doesn't know — which school —
 * then the account lands PENDING, same as email/password registration. */
export function CompleteProfilePage() {
  const { needsOnboarding, oauthProfile, loading, refreshUser } = useAuth()
  const navigate = useNavigate()
  const schools = usePublicSchools()
  const completeProfile = useCompleteOAuthProfile()

  const [displayName, setDisplayName] = useState(oauthProfile?.displayName ?? '')
  const [schoolId, setSchoolId] = useState('')
  const [error, setError] = useState<string | null>(null)

  if (loading) return <p>Loading…</p>
  if (!needsOnboarding) return <Navigate to="/" replace />

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!schoolId) {
      setError('Please select your school.')
      return
    }
    try {
      await completeProfile.mutateAsync({ display_name: displayName, school_id: schoolId })
      await refreshUser()
      navigate('/')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not complete your profile.')
    }
  }

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <h1>Just one more step</h1>
        <p className="auth-subtitle">
          {oauthProfile?.email ?? 'Your Google account'} is verified. Tell us your school to finish
          setting up your TimeForge account.
        </p>

        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="profile-name">Full name</label>
            <input
              id="profile-name"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="profile-school">School</label>
            <select
              id="profile-school"
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

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={completeProfile.isPending}
          >
            {completeProfile.isPending ? 'Finishing up…' : 'Continue'}
          </button>
        </form>
      </div>
    </main>
  )
}
