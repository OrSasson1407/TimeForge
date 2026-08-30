import { useState } from 'react'
import type { FormEvent } from 'react'
import {
  EmailAuthProvider,
  reauthenticateWithCredential,
  signOut as firebaseSignOut,
  updatePassword,
} from 'firebase/auth'
import { auth } from '../services/firebaseAuth'
import { authApi } from '../services/authApi'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'
import { showToast } from '../state/toastStore'
import { PasswordStrengthMeter, passwordMeetsAllRules } from '../components/PasswordStrengthMeter'
import { ConfirmDialog } from '../components/ConfirmDialog'

export function SecurityPage() {
  const { user } = useAuth()
  const { t } = useLanguage()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [changingPassword, setChangingPassword] = useState(false)

  const [confirmingRevoke, setConfirmingRevoke] = useState(false)
  const [revoking, setRevoking] = useState(false)

  const isGoogleAccount = auth.currentUser?.providerData.some((p) => p.providerId === 'google.com')

  async function handleChangePassword(event: FormEvent) {
    event.preventDefault()
    setPasswordError(null)

    if (!passwordMeetsAllRules(newPassword)) {
      setPasswordError(t('security.errorWeakPassword'))
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError(t('security.errorPasswordMismatch'))
      return
    }
    const firebaseUser = auth.currentUser
    if (!firebaseUser?.email) return

    setChangingPassword(true)
    try {
      await reauthenticateWithCredential(
        firebaseUser,
        EmailAuthProvider.credential(firebaseUser.email, currentPassword),
      )
      await updatePassword(firebaseUser, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      showToast({ type: 'success', message: t('security.passwordChanged') })
    } catch {
      setPasswordError(t('security.errorCurrentPasswordWrong'))
    } finally {
      setChangingPassword(false)
    }
  }

  async function handleRevokeSessions() {
    setConfirmingRevoke(false)
    setRevoking(true)
    try {
      await authApi.revokeSessions()
      showToast({ type: 'success', message: t('security.sessionsRevoked') })
      await firebaseSignOut(auth)
    } catch {
      showToast({ type: 'error', message: t('security.errorRevokeFailed') })
      setRevoking(false)
    }
  }

  return (
    <main>
      <h2>{t('security.title')}</h2>
      <p>{t('security.subtitle')}</p>

      {!isGoogleAccount && (
        <section className="auth-card" style={{ maxWidth: 480, margin: '1rem 0' }}>
          <h3 style={{ marginTop: 0 }}>{t('security.changePassword')}</h3>
          <form onSubmit={handleChangePassword}>
            {passwordError && (
              <div className="alert alert-danger" role="alert">
                {passwordError}
              </div>
            )}
            <div className="field">
              <label htmlFor="security-current-password">{t('security.currentPassword')}</label>
              <input
                id="security-current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            <div className="field">
              <label htmlFor="security-new-password">{t('security.newPassword')}</label>
              <input
                id="security-new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
              <PasswordStrengthMeter password={newPassword} />
            </div>
            <div className="field">
              <label htmlFor="security-confirm-password">{t('security.confirmNewPassword')}</label>
              <input
                id="security-confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={changingPassword}>
              {changingPassword ? t('security.changingPassword') : t('security.changePassword')}
            </button>
          </form>
        </section>
      )}

      {isGoogleAccount && (
        <section className="auth-card" style={{ maxWidth: 480, margin: '1rem 0' }}>
          <h3 style={{ marginTop: 0 }}>{t('security.changePassword')}</h3>
          <p>{t('security.googleAccountNotice')}</p>
        </section>
      )}

      <section className="auth-card" style={{ maxWidth: 480, margin: '1rem 0' }}>
        <h3 style={{ marginTop: 0 }}>{t('security.sessions')}</h3>
        <p>{t('security.sessionsDescription')}</p>
        {user && (
          <p className="field-hint">
            {t('security.signedInAs')} {user.display_name}
          </p>
        )}
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => setConfirmingRevoke(true)}
          disabled={revoking}
        >
          {revoking ? t('security.revoking') : t('security.revokeSessions')}
        </button>
      </section>

      {confirmingRevoke && (
        <ConfirmDialog
          title={t('security.revokeConfirmTitle')}
          message={t('security.revokeConfirmMessage')}
          confirmLabel={t('security.revokeSessions')}
          danger
          onConfirm={() => void handleRevokeSessions()}
          onCancel={() => setConfirmingRevoke(false)}
        />
      )}
    </main>
  )
}
