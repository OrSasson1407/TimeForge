/**
 * Offline-first cache for the timetable.
 *
 * The corridor problem this exists for: a teacher opens the app between
 * lessons, somewhere with no usable signal. Showing a spinner that never
 * resolves is the wrong answer — the timetable changes at most a few times
 * a term, so a cached copy is almost always still correct. The screen
 * therefore renders whatever is cached immediately and refreshes behind it,
 * rather than blocking on the network.
 *
 * The store is injected rather than importing AsyncStorage directly, so
 * this is unit-testable in Node with a plain in-memory map — no simulator,
 * no native module.
 */

import type { MyTimetable } from '../api/types'

export interface KeyValueStore {
  getItem(key: string): Promise<string | null>
  setItem(key: string, value: string): Promise<void>
  removeItem(key: string): Promise<void>
}

export interface CachedTimetable {
  timetable: MyTimetable
  /** Epoch ms, so the UI can say how stale what it is showing might be. */
  cachedAt: number
}

const KEY_PREFIX = 'timeforge.timetable.'

/** Namespaced per user: a shared or handed-on device must never show one
 * teacher the other's lessons after a sign-out. */
function keyFor(userId: string): string {
  return `${KEY_PREFIX}${userId}`
}

export function createTimetableCache(store: KeyValueStore) {
  return {
    async read(userId: string): Promise<CachedTimetable | null> {
      const raw = await store.getItem(keyFor(userId))
      if (!raw) return null
      try {
        const parsed = JSON.parse(raw) as CachedTimetable
        // Guard against a cache written by an older app version whose shape
        // has since changed: a corrupt read must degrade to "no cache", not
        // crash the only screen the app has.
        if (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.timetable?.entries)) {
          return null
        }
        return parsed
      } catch {
        return null
      }
    },

    async write(userId: string, timetable: MyTimetable, now: number = Date.now()): Promise<void> {
      const payload: CachedTimetable = { timetable, cachedAt: now }
      try {
        await store.setItem(keyFor(userId), JSON.stringify(payload))
      } catch {
        // A full disk must not break a session that is otherwise working —
        // the app just loses its offline copy until the next successful write.
      }
    },

    async clear(userId: string): Promise<void> {
      try {
        await store.removeItem(keyFor(userId))
      } catch {
        // Best-effort; see write().
      }
    },
  }
}

export type TimetableCache = ReturnType<typeof createTimetableCache>
