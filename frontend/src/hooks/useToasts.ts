import { useSyncExternalStore } from 'react'
import { getToasts, subscribeToasts } from '../state/toastStore'

export function useToasts() {
  return useSyncExternalStore(subscribeToasts, getToasts, getToasts)
}
