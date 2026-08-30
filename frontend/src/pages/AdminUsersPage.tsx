import { useMemo, useState } from 'react'
import { useReactivateUser, useSuspendUser, useUsers } from '../hooks/useAuthFlow'
import { ApiError } from '../services/apiClient'
import { showToast } from '../state/toastStore'
import { EmptyState, ErrorState, SkeletonTable } from '../components/AsyncState'
import { ConfirmDialog } from '../components/ConfirmDialog'
import type { AdminUser } from '../types/auth'

export function AdminUsersPage() {
  const users = useUsers(true)
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    if (!users.data) return undefined
    const needle = query.trim().toLowerCase()
    if (!needle) return users.data
    return users.data.filter(
      (user) =>
        user.display_name.toLowerCase().includes(needle) ||
        user.email.toLowerCase().includes(needle),
    )
  }, [users.data, query])

  return (
    <main>
      <h2>Manage users</h2>
      <p>Suspend or reactivate an existing Admin or Teacher account.</p>

      {users.isLoading && <SkeletonTable rows={4} columns={5} />}
      {users.isError && (
        <ErrorState message="Could not load users." onRetry={() => void users.refetch()} />
      )}
      {users.data?.length === 0 && (
        <EmptyState
          title="No users yet"
          message="Admins and teachers will show up here once approved."
        />
      )}

      {users.data && users.data.length > 0 && (
        <>
          {users.data.length > 5 && (
            <div className="field" style={{ maxWidth: 320 }}>
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by name or email…"
                aria-label="Search users"
              />
            </div>
          )}

          {filtered?.length === 0 ? (
            <p>No matches for "{query}".</p>
          ) : (
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
                {filtered?.map((user) => (
                  <UserRow key={user.id} user={user} />
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </main>
  )
}

function UserRow({ user }: { user: AdminUser }) {
  const suspend = useSuspendUser()
  const reactivate = useReactivateUser()
  const [error, setError] = useState<string | null>(null)
  const [confirmingSuspend, setConfirmingSuspend] = useState(false)

  async function handleSuspend() {
    setConfirmingSuspend(false)
    setError(null)
    try {
      await suspend.mutateAsync(user.id)
      showToast({ type: 'success', message: `${user.display_name} suspended.` })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Action failed.')
    }
  }

  async function handleReactivate() {
    setError(null)
    try {
      await reactivate.mutateAsync(user.id)
      showToast({ type: 'success', message: `${user.display_name} reactivated.` })
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
          onClick={() => (user.is_active ? setConfirmingSuspend(true) : void handleReactivate())}
          disabled={busy}
        >
          {user.is_active ? 'Suspend' : 'Reactivate'}
        </button>
      </td>

      {confirmingSuspend && (
        <ConfirmDialog
          title="Suspend this account?"
          message={`${user.display_name} will immediately lose access — their Firebase account is disabled and every request is rejected until you reactivate them.`}
          confirmLabel="Suspend"
          danger
          onConfirm={() => void handleSuspend()}
          onCancel={() => setConfirmingSuspend(false)}
        />
      )}
    </tr>
  )
}
