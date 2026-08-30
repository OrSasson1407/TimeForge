import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { authApi } from '../services/authApi'
import type { User } from '../types/auth'

const { authStateCallback } = vi.hoisted(() => ({
  authStateCallback: { current: null as ((user: unknown) => void) | null },
}))

vi.mock('../services/firebaseAuth', () => ({ auth: {} }))

vi.mock('firebase/auth', () => ({
  onAuthStateChanged: (_auth: unknown, callback: (user: unknown) => void) => {
    authStateCallback.current = callback
    return () => {}
  },
  signInWithEmailAndPassword: vi.fn(),
  signOut: vi.fn(),
}))

vi.mock('../services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/apiClient')>()
  return {
    ...actual,
    apiClient: { get: vi.fn().mockResolvedValue({ status: 'ok' }) },
  }
})

vi.mock('../services/authApi', () => ({ authApi: { me: vi.fn() } }))

describe('App', () => {
  beforeEach(() => {
    // BrowserRouter reads the real jsdom history, which persists across
    // tests in this file (unlike component state) — reset it so each test
    // starts from "/" instead of wherever the previous test's redirect left it.
    window.history.pushState({}, '', '/')
  })

  it('redirects unauthenticated users to the login page', async () => {
    render(<App />)

    authStateCallback.current!(null)

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Welcome back' })).toBeInTheDocument(),
    )
  })

  it('shows the dashboard once a Firebase identity resolves to a TimeForge user', async () => {
    const adminUser: User = {
      id: 'admin_1',
      role: 'ADMIN',
      school_id: 's1',
      display_name: 'Dana Admin',
      teacher_id: null,
      email_verified: true,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    }
    vi.mocked(authApi.me).mockResolvedValue(adminUser)

    render(<App />)
    authStateCallback.current!({ uid: 'admin_1' })

    await waitFor(() => expect(screen.getByText(/Welcome, Dana Admin/)).toBeInTheDocument())
    expect(screen.getByRole('link', { name: /Manage teachers/ })).toBeInTheDocument()
  })

  it('hides admin-only navigation from a teacher', async () => {
    const teacherUser: User = {
      id: 'teacher_1',
      role: 'TEACHER',
      school_id: 's1',
      display_name: 'Tal Teacher',
      teacher_id: 't1',
      email_verified: true,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    }
    vi.mocked(authApi.me).mockResolvedValue(teacherUser)

    render(<App />)
    authStateCallback.current!({ uid: 'teacher_1' })

    await waitFor(() => expect(screen.getByText(/Welcome, Tal Teacher/)).toBeInTheDocument())
    expect(screen.queryByRole('link', { name: 'Management' })).not.toBeInTheDocument()
  })
})
