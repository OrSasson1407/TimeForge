import { useSyncExternalStore } from 'react'

function subscribe(callback: () => void) {
  window.addEventListener('online', callback)
  window.addEventListener('offline', callback)
  return () => {
    window.removeEventListener('online', callback)
    window.removeEventListener('offline', callback)
  }
}

function getSnapshot() {
  return navigator.onLine
}

/** True when the browser reports connectivity. Backs the offline banner
 * and the "you're offline" wording swapped in for network-level errors
 * (see app/queryClient.ts). Server snapshot assumes online, since SSR
 * isn't in play here but useSyncExternalStore requires one. */
export function useOnlineStatus(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, () => true)
}
