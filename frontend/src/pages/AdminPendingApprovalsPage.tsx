import { useState } from 'react'
import { teacherHooks } from '../hooks/useCatalog'
import { useApproveUser, usePendingUsers, useRejectUser } from '../hooks/useAuthFlow'
import { ApiError } from '../services/apiClient'
import { showToast } from '../state/toastStore'
import { EmptyState, ErrorState, Spinner } from '../components/AsyncState'
import { ConfirmDialog } from '../components/ConfirmDialog'
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
  const approve = useApproveUser()
  const reject = useRejectUser()
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [confirmingBulkReject, setConfirmingBulkReject] = useState(false)
  const [bulkBusy, setBulkBusy] = useState(false)

  const sorted = pending.data
    ? [...pending.data].sort(
        (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      )
    : undefined

  function toggleSelected(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    if (!sorted) return
    setSelected((prev) =>
      prev.size === sorted.length ? new Set() : new Set(sorted.map((u) => u.id)),
    )
  }

  async function handleBulkApproveAsAdmin() {
    setBulkBusy(true)
    const ids = [...selected]
    let succeeded = 0
    for (const id of ids) {
      try {
        await approve.mutateAsync({ userId: id, body: { role: 'ADMIN', teacher_id: null } })
        succeeded++
      } catch {
        // one failure shouldn't stop the rest; the toast summary reports the shortfall
      }
    }
    setBulkBusy(false)
    setSelected(new Set())
    showToast({
      type: succeeded === ids.length ? 'success' : 'error',
      message:
        succeeded === ids.length
          ? `Approved ${succeeded} account(s) as admin.`
          : `Approved ${succeeded} of ${ids.length} account(s) — some failed.`,
    })
  }

  async function handleBulkReject() {
    setConfirmingBulkReject(false)
    setBulkBusy(true)
    const ids = [...selected]
    let succeeded = 0
    for (const id of ids) {
      try {
        await reject.mutateAsync(id)
        succeeded++
      } catch {
        // one failure shouldn't stop the rest; the toast summary reports the shortfall
      }
    }
    setBulkBusy(false)
    setSelected(new Set())
    showToast({
      type: succeeded === ids.length ? 'info' : 'error',
      message:
        succeeded === ids.length
          ? `Rejected ${succeeded} registration(s).`
          : `Rejected ${succeeded} of ${ids.length} account(s) — some failed.`,
    })
  }

  return (
    <main>
      <h2>Pending approvals</h2>
      <p>
        Newly registered accounts wait here, verified but powerless, until you assign them a role.
      </p>

      {pending.isLoading && <Spinner label="Loading pending approvals" />}
      {pending.isError && (
        <ErrorState
          message="Could not load pending approvals."
          onRetry={() => void pending.refetch()}
        />
      )}
      {sorted?.length === 0 && (
        <EmptyState
          title="Nothing to review"
          message="No accounts are waiting for approval right now."
        />
      )}

      {sorted && sorted.length > 1 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            margin: '0.75rem 0',
            flexWrap: 'wrap',
          }}
        >
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4em' }}>
            <input
              type="checkbox"
              checked={selected.size === sorted.length}
              onChange={toggleSelectAll}
              aria-label="Select all pending accounts"
            />
            Select all
          </label>
          {selected.size > 0 && (
            <>
              <span className="field-hint">{selected.size} selected</span>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => void handleBulkApproveAsAdmin()}
                disabled={bulkBusy}
              >
                Approve selected as Admin
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setConfirmingBulkReject(true)}
                disabled={bulkBusy}
              >
                Reject selected
              </button>
            </>
          )}
        </div>
      )}

      <div style={{ display: 'grid', gap: '1rem' }}>
        {sorted?.map((user) => (
          <ApprovalCard
            key={user.id}
            user={user}
            selectable={sorted.length > 1}
            selected={selected.has(user.id)}
            onToggleSelected={() => toggleSelected(user.id)}
          />
        ))}
      </div>

      {confirmingBulkReject && (
        <ConfirmDialog
          title={`Reject ${selected.size} registration(s)?`}
          message="Every selected account will be permanently deleted, including its Firebase Auth account. This can't be undone."
          confirmLabel="Reject all"
          danger
          onConfirm={() => void handleBulkReject()}
          onCancel={() => setConfirmingBulkReject(false)}
        />
      )}
    </main>
  )
}

function ApprovalCard({
  user,
  selectable,
  selected,
  onToggleSelected,
}: {
  user: PendingUser
  selectable: boolean
  selected: boolean
  onToggleSelected: () => void
}) {
  const teachers = teacherHooks.useList(user.school_id)
  const approve = useApproveUser()
  const reject = useRejectUser()

  const [role, setRole] = useState<'TEACHER' | 'ADMIN'>('TEACHER')
  const [teacherId, setTeacherId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [confirmingReject, setConfirmingReject] = useState(false)

  async function handleApprove() {
    setError(null)
    try {
      await approve.mutateAsync({
        userId: user.id,
        body: { role, teacher_id: role === 'TEACHER' ? teacherId || null : null },
      })
      showToast({
        type: 'success',
        message: `${user.display_name} approved as ${role.toLowerCase()}.`,
      })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not approve this account.')
    }
  }

  async function handleReject() {
    setConfirmingReject(false)
    setError(null)
    try {
      await reject.mutateAsync(user.id)
      showToast({ type: 'info', message: `${user.display_name}'s registration was rejected.` })
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
        {selectable && (
          <input
            type="checkbox"
            checked={selected}
            onChange={onToggleSelected}
            aria-label={`Select ${user.display_name}`}
          />
        )}
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
          onClick={() => setConfirmingReject(true)}
          disabled={busy}
        >
          Reject
        </button>
      </div>

      {confirmingReject && (
        <ConfirmDialog
          title="Reject this registration?"
          message={`${user.display_name}'s account will be permanently deleted, including their Firebase Auth account. This can't be undone — they'd need to register again.`}
          confirmLabel="Reject"
          danger
          onConfirm={() => void handleReject()}
          onCancel={() => setConfirmingReject(false)}
        />
      )}
    </div>
  )
}
