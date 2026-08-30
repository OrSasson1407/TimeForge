import { Link } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useSchool } from '../hooks/useSchool'
import { classHooks, roomHooks, teacherHooks } from '../hooks/useCatalog'
import { useSchedule, useScheduleVersion } from '../hooks/useSchedule'
import { usePendingUsers } from '../hooks/useAuthFlow'

export function DashboardPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'ADMIN'
  const { data: school } = useSchool(user?.school_id)
  const teachers = teacherHooks.useList(user?.school_id)
  const classes = classHooks.useList(user?.school_id)
  const rooms = roomHooks.useList(user?.school_id)
  const { data: schedule } = useSchedule(user?.school_id)
  const { data: activeVersion } = useScheduleVersion(
    user?.school_id,
    schedule?.active_version_id ?? undefined,
  )
  const pending = usePendingUsers(isAdmin)

  const teacherCount = teachers.data?.length ?? 0
  const classCount = classes.data?.length ?? 0
  const roomCount = rooms.data?.length ?? 0
  const hasSchedule = Boolean(schedule?.active_version_id)

  const setupSteps = [
    { done: teacherCount > 0, label: 'Add your teachers', to: '/management' },
    { done: classCount > 0, label: 'Add your classes', to: '/management' },
    { done: roomCount > 0, label: 'Add your rooms', to: '/management' },
    { done: hasSchedule, label: 'Generate your first schedule', to: '/schedule' },
  ]
  const setupIncomplete = isAdmin && setupSteps.some((step) => !step.done)

  return (
    <main>
      <h2>Welcome, {user?.display_name}</h2>
      <p>{school ? school.name : 'Loading school…'}</p>

      {setupIncomplete && (
        <section className="auth-card" style={{ maxWidth: 480, margin: '1rem 0' }}>
          <h3 style={{ marginTop: 0 }}>Get your school set up</h3>
          <ul style={{ listStyle: 'none', padding: 0, display: 'grid', gap: '0.5em' }}>
            {setupSteps.map((step) => (
              <li key={step.label}>
                {step.done ? (
                  <span style={{ color: 'var(--color-success)' }}>✓ {step.label}</span>
                ) : (
                  <Link to={step.to}>○ {step.label}</Link>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {isAdmin && (
        <section style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', margin: '1rem 0' }}>
          <StatCard label="Teachers" value={teacherCount} />
          <StatCard label="Classes" value={classCount} />
          <StatCard label="Rooms" value={roomCount} />
          <StatCard
            label="Schedule quality"
            value={activeVersion?.score ? `${Math.round(activeVersion.score.quality)}/100` : '—'}
          />
          {pending.data && pending.data.length > 0 && (
            <StatCard
              label="Pending approvals"
              value={pending.data.length}
              to="/pending-approvals"
            />
          )}
        </section>
      )}

      <ul>
        <li>
          <Link to="/schedule">View the timetable</Link>
        </li>
        <li>
          <Link to="/availability">
            {user?.role === 'ADMIN' ? 'Manage availability' : 'Submit your availability'}
          </Link>
        </li>
        {user?.role === 'ADMIN' && (
          <>
            <li>
              <Link to="/management">Manage teachers, classes, rooms, and subjects</Link>
            </li>
            <li>
              <Link to="/constraints">Configure constraint weights</Link>
            </li>
            <li>
              <Link to="/audit">View the audit log</Link>
            </li>
          </>
        )}
      </ul>
    </main>
  )
}

function StatCard({ label, value, to }: { label: string; value: string | number; to?: string }) {
  const content = (
    <div
      className="auth-card"
      style={{ maxWidth: 'none', margin: 0, padding: '1rem 1.25rem', minWidth: 140 }}
    >
      <div className="label-mono">{label}</div>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 600 }}>
        {value}
      </div>
    </div>
  )
  return to ? (
    <Link to={to} style={{ textDecoration: 'none', color: 'inherit' }}>
      {content}
    </Link>
  ) : (
    content
  )
}
