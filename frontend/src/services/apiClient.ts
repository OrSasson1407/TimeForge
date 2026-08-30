/**
 * Thin typed wrapper around fetch() for calling the TimeForge backend.
 * The frontend never talks to Firestore directly for business data — every
 * mutation and every business read goes through this client (see
 * docs/01-CLAUDE.md rule 6, docs/03-ARCHITECTURE.md #8).
 *
 * Every request attaches the current Firebase ID token as a Bearer header
 * when one is available — the backend's `get_current_user` dependency
 * requires it for every route except /health (docs/03-ARCHITECTURE.md
 * #23-24). A failed response is parsed as the backend's structured
 * ErrorEnvelope (docs/04-DESIGN.md #"Error Model") so callers get the same
 * `type`/`message` the backend produced, not a generic HTTP status.
 */
import { auth } from './firebaseAuth'
import type { ErrorEnvelope } from '../types/common'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  readonly status: number
  readonly type: string
  readonly details: Record<string, unknown>

  constructor(status: number, type: string, message: string, details: Record<string, unknown>) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.type = type
    this.details = details
  }
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  return (
    typeof value === 'object' &&
    value !== null &&
    'error' in value &&
    typeof (value as { error: unknown }).error === 'object'
  )
}

async function buildApiError(response: Response): Promise<ApiError> {
  let body: unknown
  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (isErrorEnvelope(body)) {
    return new ApiError(response.status, body.error.type, body.error.message, body.error.details)
  }
  return new ApiError(
    response.status,
    'UnknownError',
    `Request failed with status ${response.status}`,
    {},
  )
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await auth.currentUser?.getIdToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...headers, ...init?.headers },
  })

  if (!response.ok) {
    throw await buildApiError(response)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
}
