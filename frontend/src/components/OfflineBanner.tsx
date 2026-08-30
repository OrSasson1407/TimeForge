import { useEffect, useRef } from 'react'
import { useOnlineStatus } from '../hooks/useOnlineStatus'
import { showToast } from '../state/toastStore'

/** Fixed banner shown whenever the browser reports no connectivity, plus a
 * one-off "back online" toast on reconnect — the "Offline / reconnect
 * states" and "Retry failed requests" UX (docs/02-PRD.md UX notes). */
export function OfflineBanner() {
  const isOnline = useOnlineStatus()
  const wasOffline = useRef(false)

  useEffect(() => {
    if (!isOnline) {
      wasOffline.current = true
    } else if (wasOffline.current) {
      wasOffline.current = false
      showToast({ type: 'success', message: "You're back online." }, 4000)
    }
  }, [isOnline])

  if (isOnline) return null

  return (
    <div className="offline-banner" role="status">
      You're offline. Changes won't save until your connection comes back.
    </div>
  )
}
