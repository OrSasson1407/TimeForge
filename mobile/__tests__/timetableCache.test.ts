import { createTimetableCache, type KeyValueStore } from '../src/storage/timetableCache'
import type { MyTimetable } from '../src/api/types'

function memoryStore(initial: Record<string, string> = {}): KeyValueStore & { data: Map<string, string> } {
  const data = new Map(Object.entries(initial))
  return {
    data,
    async getItem(key) {
      return data.get(key) ?? null
    },
    async setItem(key, value) {
      data.set(key, value)
    },
    async removeItem(key) {
      data.delete(key)
    },
  }
}

const timetable: MyTimetable = {
  version_id: 'v1',
  entries: [
    {
      assignment_id: 'a1',
      day_id: 'day_mon',
      weekday: 'MONDAY',
      time_period_id: 'p1',
      period_index: 0,
      start_time: '08:00:00',
      end_time: '08:45:00',
      class_name: '7A',
      room_name: 'Room 1',
      subject_code: 'MATH',
      subject_name: 'Mathematics',
    },
  ],
}

describe('timetable cache', () => {
  it('round-trips a timetable with the time it was cached', async () => {
    const cache = createTimetableCache(memoryStore())

    await cache.write('user-1', timetable, 1_700_000_000_000)
    const cached = await cache.read('user-1')

    expect(cached?.timetable).toEqual(timetable)
    expect(cached?.cachedAt).toBe(1_700_000_000_000)
  })

  it('returns null when nothing has been cached', async () => {
    const cache = createTimetableCache(memoryStore())

    expect(await cache.read('user-1')).toBeNull()
  })

  it('keeps each user’s copy separate', async () => {
    const cache = createTimetableCache(memoryStore())

    await cache.write('teacher-a', timetable)

    expect(await cache.read('teacher-b')).toBeNull()
  })

  it('clears only the requested user', async () => {
    const cache = createTimetableCache(memoryStore())
    await cache.write('teacher-a', timetable)
    await cache.write('teacher-b', timetable)

    await cache.clear('teacher-a')

    expect(await cache.read('teacher-a')).toBeNull()
    expect(await cache.read('teacher-b')).not.toBeNull()
  })

  it('degrades to "no cache" on unparseable data rather than throwing', async () => {
    const cache = createTimetableCache(memoryStore({ 'timeforge.timetable.user-1': 'not json' }))

    expect(await cache.read('user-1')).toBeNull()
  })

  it('rejects a cache whose shape no longer matches (older app version)', async () => {
    const stale = JSON.stringify({ timetable: { version_id: 'v1' }, cachedAt: 1 })
    const cache = createTimetableCache(memoryStore({ 'timeforge.timetable.user-1': stale }))

    expect(await cache.read('user-1')).toBeNull()
  })

  it('survives a store that refuses to write', async () => {
    const failing: KeyValueStore = {
      async getItem() {
        return null
      },
      async setItem() {
        throw new Error('disk full')
      },
      async removeItem() {
        throw new Error('disk full')
      },
    }
    const cache = createTimetableCache(failing)

    // The session keeps working; only the offline copy is lost.
    await expect(cache.write('user-1', timetable)).resolves.toBeUndefined()
    await expect(cache.clear('user-1')).resolves.toBeUndefined()
  })
})
