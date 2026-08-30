import { Link } from 'react-router-dom'
import { usePendingUsers } from '../hooks/useAuthFlow'
import { useAuth } from '../state/AuthContext'

/** A persistent count of pending registrations, complementing the
 * transient toasts — an admin who hasn't looked at the approvals queue in
 * a while has no other passive signal that something is waiting. */
export function NotificationBell() {
  const { user } = useAuth()
  const pending = usePendingUsers(user?.role === 'ADMIN')
  const count = pending.data?.length ?? 0

  if (user?.role !== 'ADMIN') return null

  return (
    <Link
      to="/pending-approvals"
      className="notification-bell"
      aria-label={count > 0 ? `${count} pending approval(s)` : 'No pending approvals'}
      title={count > 0 ? `${count} pending approval(s)` : 'No pending approvals'}
    >
      <span aria-hidden="true">🔔</span>
      {count > 0 && <span className="notification-count">{count > 9 ? '9+' : count}</span>}
    </Link>
  )
}
