/**
 * Typed client for the TimeForge API.
 *
 * `getToken` and `fetchImpl` are injected rather than imported so this is
 * unit-testable in Node — the alternative (reaching for the Firebase
 * singleton internally) would make every test of this file need a native
 * module and a signed-in user.
 */

import type { CurrentUser, MyTimetable } from './types'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export interface ApiClientOptions {
  baseUrl: string
  getToken: () => Promise<string | null>
  fetchImpl?: typeof fetch
}

interface ErrorEnvelope {
  error?: { message?: string }
}

export function createApiClient({ baseUrl, getToken, fetchImpl }: ApiClientOptions) {
  const doFetch = fetchImpl ?? fetch

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const token = await getToken()
    const response = await doFetch(`${baseUrl}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init?.headers,
      },
    })

    if (!response.ok) {
      // Surface the backend's own message where it sent one — its errors are
      // written for humans ("This code has expired"), and replacing them
      // with a status code would be a downgrade.
      let message = `Request failed with status ${response.status}`
      try {
        const body = (await response.json()) as ErrorEnvelope
        if (body?.error?.message) message = body.error.message
      } catch {
        // Non-JSON body; the status-code message stands.
      }
      throw new ApiError(response.status, message)
    }

    if (response.status === 204) return undefined as T
    return (await response.json()) as T
  }

  return {
    me: () => request<CurrentUser>('/auth/me'),

    myTimetable: (schoolId: string) =>
      request<MyTimetable>(`/schedules/my-timetable?school_id=${encodeURIComponent(schoolId)}`),

    registerDevice: (token: string, platform: 'IOS' | 'ANDROID') =>
      request<{ message: string }>('/notifications/devices', {
        method: 'POST',
        body: JSON.stringify({ token, platform }),
      }),

    unregisterDevice: (token: string) =>
      request<{ message: string }>(`/notifications/devices/${encodeURIComponent(token)}`, {
        method: 'DELETE',
      }),
  }
}

export type ApiClient = ReturnType<typeof createApiClient>
