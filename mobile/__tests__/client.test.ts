import { ApiError, createApiClient } from '../src/api/client'

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as unknown as Response
}

describe('api client', () => {
  it('attaches the bearer token', async () => {
    const calls: Array<[string, RequestInit | undefined]> = []
    const client = createApiClient({
      baseUrl: 'https://api.example',
      getToken: async () => 'tok-123',
      fetchImpl: (async (url: string, init?: RequestInit) => {
        calls.push([url, init])
        return jsonResponse({ version_id: null, entries: [] })
      }) as unknown as typeof fetch,
    })

    await client.myTimetable('school-1')

    const [url, init] = calls[0]
    expect(url).toBe('https://api.example/schedules/my-timetable?school_id=school-1')
    expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer tok-123')
  })

  it('omits the header entirely when signed out, rather than sending "Bearer null"', async () => {
    let seen: RequestInit | undefined
    const client = createApiClient({
      baseUrl: 'https://api.example',
      getToken: async () => null,
      fetchImpl: (async (_url: string, init?: RequestInit) => {
        seen = init
        return jsonResponse({ version_id: null, entries: [] })
      }) as unknown as typeof fetch,
    })

    await client.myTimetable('school-1')

    expect((seen?.headers as Record<string, string>).Authorization).toBeUndefined()
  })

  it('url-encodes the school id', async () => {
    let seenUrl = ''
    const client = createApiClient({
      baseUrl: 'https://api.example',
      getToken: async () => 't',
      fetchImpl: (async (url: string) => {
        seenUrl = url
        return jsonResponse({ version_id: null, entries: [] })
      }) as unknown as typeof fetch,
    })

    await client.myTimetable('a b&c')

    expect(seenUrl).toContain('school_id=a%20b%26c')
  })

  it('raises the backend’s own error message', async () => {
    const client = createApiClient({
      baseUrl: 'https://api.example',
      getToken: async () => 't',
      fetchImpl: (async () =>
        jsonResponse({ error: { message: 'This account has been suspended' } }, 401)) as unknown as typeof fetch,
    })

    await expect(client.myTimetable('s1')).rejects.toThrow('This account has been suspended')
  })

  it('falls back to the status code when the body is not an error envelope', async () => {
    const client = createApiClient({
      baseUrl: 'https://api.example',
      getToken: async () => 't',
      fetchImpl: (async () =>
        ({
          ok: false,
          status: 502,
          json: async () => {
            throw new Error('not json')
          },
        }) as unknown as Response) as unknown as typeof fetch,
    })

    await expect(client.myTimetable('s1')).rejects.toMatchObject({
      status: 502,
      message: 'Request failed with status 502',
    })
  })

  it('posts a device registration', async () => {
    let seen: [string, RequestInit | undefined] = ['', undefined]
    const client = createApiClient({
      baseUrl: 'https://api.example',
      getToken: async () => 't',
      fetchImpl: (async (url: string, init?: RequestInit) => {
        seen = [url, init]
        return jsonResponse({ message: 'ok' })
      }) as unknown as typeof fetch,
    })

    await client.registerDevice('fcm-abc', 'ANDROID')

    expect(seen[0]).toBe('https://api.example/notifications/devices')
    expect(seen[1]?.method).toBe('POST')
    expect(JSON.parse(String(seen[1]?.body))).toEqual({ token: 'fcm-abc', platform: 'ANDROID' })
  })

  it('exposes ApiError so callers can branch on status', async () => {
    const client = createApiClient({
      baseUrl: 'https://api.example',
      getToken: async () => 't',
      fetchImpl: (async () => jsonResponse({}, 403)) as unknown as typeof fetch,
    })

    await expect(client.myTimetable('s1')).rejects.toBeInstanceOf(ApiError)
  })
})
