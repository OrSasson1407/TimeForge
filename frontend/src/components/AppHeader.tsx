import { NavLink } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { BackendStatusBadge } from './BackendStatusBadge'

export function AppHeader() {
  const { user, signOut } = useAuth()

  return (
    <header>
      <h1>TimeForge</h1>
      <BackendStatusBadge />
      {user && user.role !== 'PENDING' && (
        <nav aria-label="Main">
          <NavLink to="/">Dashboard</NavLink>
          <NavLink to="/schedule">Schedule</NavLink>
          <NavLink to="/availability">Availability</NavLink>
          {user.role === 'ADMIN' && (
            <>
              <NavLink to="/management">Management</NavLink>
              <NavLink to="/constraints">Constraints</NavLink>
              <NavLink to="/audit">Audit Log</NavLink>
              <NavLink to="/pending-approvals">Pending Approvals</NavLink>
              <NavLink to="/users">Manage Users</NavLink>
            </>
          )}
          <span>
            {user.display_name} ({user.role})
          </span>
          <button type="button" onClick={() => void signOut()}>
            Sign out
          </button>
        </nav>
      )}
      {user && user.role === 'PENDING' && (
        <nav aria-label="Main">
          <span>{user.display_name} (awaiting approval)</span>
          <button type="button" onClick={() => void signOut()}>
            Sign out
          </button>
        </nav>
      )}
    </header>
  )
}
