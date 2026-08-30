/**
 * `localStorage` access that never throws. Real browsers can reject it
 * (Safari private browsing, cookies/storage blocked by policy, sandboxed
 * iframes) — a preference toggle failing to persist shouldn't take the
 * app down with it, it should just silently fall back to defaults.
 */
export const safeStorage = {
  get(key: string): string | null {
    try {
      return window.localStorage.getItem(key)
    } catch {
      return null
    }
  },
  set(key: string, value: string): void {
    try {
      window.localStorage.setItem(key, value)
    } catch {
      // ignore — see module docstring
    }
  },
  remove(key: string): void {
    try {
      window.localStorage.removeItem(key)
    } catch {
      // ignore — see module docstring
    }
  },
}
