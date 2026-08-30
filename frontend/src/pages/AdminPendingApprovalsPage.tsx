import { useState } from 'react'
import { teacherHooks } from '../hooks/useCatalog'
import { useApproveUser, usePendingUsers, useRejectUser } from '../hooks/useAuthFlow'
import { ApiError } from '../services/apiClient'
import type { PendingUser } from '../types/auth'

/** Registrations waiting longer than this are flagged — a stale queue is
 * easy to miss otherwise, since nothing else nudges an admin to look. */
const STALE_AFTER_DAYS = 3

function daysPending(createdAt: string): number {
  const elapsedMs = Date.now() - new Date(createdAt).getTime()
  return Math.max(Math.floor(elapsedMs / (1000 * 60 * 60 * 24)), 0)
}

export function AdminPendingApprovalsPage() {
  const pending = usePendingUsers(true)
  const sorted = pending.data
    ? [...pending.data].sort(
        (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      )
    : undefined

  return (
    <main>
      <h1>Pending approvals</h1>
      <p>
        Newly registered accounts wait here, verified but powerless, until you assign them a role.
      </p>

      {pending.isLoading && <p>Loading…</p>}
      {sorted?.length === 0 && <p>No accounts are waiting for approval.</p>}

      <div style={{ display: 'grid', gap: '1rem' }}>
        {sorted?.map((user) => (
          <ApprovalCard key={user.id} user={user} />
        ))}
      </div>
    </main>
  )
}

function ApprovalCard({ user }: { user: PendingUser }) {
  const teachers = teacherHooks.useList(user.school_id)
  const approve = useApproveUser()
  const reject = useRejectUser()

  const [role, setRole] = useState<'TEACHER' | 'ADMIN'>('TEACHER')
  const [teacherId, setTeacherId] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function handleApprove() {
    setError(null)
    try {
      await approve.mutateAsync({
        userId: user.id,
        body: { role, teacher_id: role === 'TEACHER' ? teacherId || null : null },
      })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not approve this account.')
    }
  }

  async function handleReject() {
    setError(null)
    try {
      await reject.mutateAsync(user.id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not reject this account.')
    }
  }

  const busy = approve.isPending || reject.isPending
  const waitingDays = daysPending(user.created_at)
  const isStale = waitingDays >= STALE_AFTER_DAYS

  return (
    <div className="auth-card" style={{ maxWidth: 'none', margin: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75em' }}>
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>{user.display_name}</h2>
        <span
          className={isStale ? 'pending-badge' : undefined}
          style={isStale ? undefined : { color: 'var(--color-text-muted)', fontSize: '0.8rem' }}
        >
          {waitingDays === 0 ? 'waiting less than a day' : `waiting ${waitingDays}d`}
        </span>
      </div>
      <p className="field-hint">
        {user.email} · school {user.school_id}
      </p>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor={`role-${user.id}`}>Role</label>
          <select
            id={`role-${user.id}`}
            value={role}
            onChange={(e) => setRole(e.target.value as 'TEACHER' | 'ADMIN')}
          >
            <option value="TEACHER">Teacher</option>
            <option value="ADMIN">Admin</option>
          </select>
        </div>

        {role === 'TEACHER' && (
          <div className="field" style={{ marginBottom: 0 }}>
            <label htmlFor={`teacher-${user.id}`}>Link to teacher record</label>
            <select
              id={`teacher-${user.id}`}
              value={teacherId}
              onChange={(e) => setTeacherId(e.target.value)}
            >
              <option value="" disabled>
                {teachers.isLoading ? 'Loading…' : 'Select a teacher'}
              </option>
              {teachers.data?.map((teacher) => (
                <option key={teacher.id} value={teacher.id}>
                  {teacher.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <button
          type="button"
          className="btn btn-primary"
          onClick={() => void handleApprove()}
          disabled={busy || (role === 'TEACHER' && !teacherId)}
        >
          Approve
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => void handleReject()}
          disabled={busy}
        >
          Reject
        </button>
      </div>
    </div>
  )
}
