import { Link } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useSchool } from '../hooks/useSchool'

export function DashboardPage() {
  const { user } = useAuth()
  const { data: school } = useSchool(user?.school_id)

  return (
    <main>
      <h2>Welcome, {user?.display_name}</h2>
      <p>{school ? school.name : 'Loading school…'}</p>
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
