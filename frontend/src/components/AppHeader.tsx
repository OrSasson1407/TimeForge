import { NavLink } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'
import { BackendStatusBadge } from './BackendStatusBadge'
import { ThemeToggle } from './ThemeToggle'
import { LanguageToggle } from './LanguageToggle'
import { NotificationBell } from './NotificationBell'

export function AppHeader() {
  const { user, signOut } = useAuth()
  const { t } = useLanguage()

  return (
    <header>
      <h1>{t('app.name')}</h1>
      <BackendStatusBadge />
      {user && user.role !== 'PENDING' && (
        <nav aria-label="Main">
          <NavLink to="/">{t('nav.dashboard')}</NavLink>
          <NavLink to="/schedule">{t('nav.schedule')}</NavLink>
          <NavLink to="/availability">{t('nav.availability')}</NavLink>
          {user.role === 'ADMIN' && (
            <>
              <NavLink to="/management">{t('nav.management')}</NavLink>
              <NavLink to="/constraints">{t('nav.constraints')}</NavLink>
              <NavLink to="/audit">{t('nav.audit')}</NavLink>
              <NavLink to="/pending-approvals">{t('nav.pendingApprovals')}</NavLink>
              <NavLink to="/users">{t('nav.manageUsers')}</NavLink>
            </>
          )}
          <NavLink to="/security">{t('nav.security')}</NavLink>
          <span>
            {user.display_name} ({user.role})
          </span>
          <NotificationBell />
          <ThemeToggle />
          <LanguageToggle />
          <button type="button" onClick={() => void signOut()}>
            {t('nav.signOut')}
          </button>
        </nav>
      )}
      {user && user.role === 'PENDING' && (
        <nav aria-label="Main">
          <span>
            {user.display_name} ({t('nav.awaitingApproval')})
          </span>
          <ThemeToggle />
          <LanguageToggle />
          <button type="button" onClick={() => void signOut()}>
            {t('nav.signOut')}
          </button>
        </nav>
      )}
      {!user && (
        <nav aria-label="Preferences">
          <ThemeToggle />
          <LanguageToggle />
        </nav>
      )}
    </header>
  )
}
