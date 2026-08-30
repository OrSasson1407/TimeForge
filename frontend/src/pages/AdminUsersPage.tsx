import { useState } from 'react'
import { useReactivateUser, useSuspendUser, useUsers } from '../hooks/useAuthFlow'
import { ApiError } from '../services/apiClient'
import type { AdminUser } from '../types/auth'

export function AdminUsersPage() {
  const users = useUsers(true)

  return (
    <main>
      <h1>Manage users</h1>
      <p>Suspend or reactivate an existing Admin or Teacher account.</p>

      {users.isLoading && <p>Loading…</p>}
      {users.data?.length === 0 && <p>No users found.</p>}

      {users.data && users.data.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Since</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.data.map((user) => (
              <UserRow key={user.id} user={user} />
            ))}
          </tbody>
        </table>
      )}
    </main>
  )
}

function UserRow({ user }: { user: AdminUser }) {
  const suspend = useSuspendUser()
  const reactivate = useReactivateUser()
  const [error, setError] = useState<string | null>(null)

  async function handleToggle() {
    setError(null)
    try {
      if (user.is_active) {
        await suspend.mutateAsync(user.id)
      } else {
        await reactivate.mutateAsync(user.id)
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Action failed.')
    }
  }

  const busy = suspend.isPending || reactivate.isPending

  return (
    <tr>
      <td>{user.display_name}</td>
      <td>{user.email}</td>
      <td>{user.role}</td>
      <td>
        <span className={user.is_active ? undefined : 'pending-badge'}>
          {user.is_active ? 'Active' : 'Suspended'}
        </span>
        {error && <div style={{ color: 'var(--color-danger)', fontSize: '0.8rem' }}>{error}</div>}
      </td>
      <td>{new Date(user.created_at).toLocaleDateString()}</td>
      <td>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => void handleToggle()}
          disabled={busy}
        >
          {user.is_active ? 'Suspend' : 'Reactivate'}
        </button>
      </td>
    </tr>
  )
}
