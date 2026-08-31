/**
 * Live collaboration on one schedule version: who else has it open, and
 * refetching automatically when one of them changes it.
 *
 * The socket carries awareness only. Every actual edit still goes through
 * the REST API, whose `version_tag` optimistic concurrency is what actually
 * prevents two admins clobbering each other (it returns 409 on a stale
 * write whether or not this hook is connected). So a dropped message costs
 * freshness, never correctness — which is why reconnection here is
 * best-effort and failures are silent rather than surfaced as errors.
 */
import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { auth } from '../services/firebaseAuth'
import { showToast } from '../state/toastStore'

export interface Participant {
  user_id: string
  display_name: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

/** Reconnect backoff, capped. Starts fast because the overwhelmingly
 * common case is a transient blip (laptop lid, wifi handover) that
 * recovers immediately. */
const RECONNECT_BASE_MS = 1000
const RECONNECT_MAX_MS = 30000

function websocketUrl(versionId: string, schoolId: string): string {
  const base = API_BASE_URL.replace(/^http/, 'ws')
  return `${base}/ws/schedules/${encodeURIComponent(versionId)}?school_id=${encodeURIComponent(schoolId)}`
}

export function useCollaboration(
  schoolId: string | undefined,
  versionId: string | undefined,
): { participants: Participant[]; connected: boolean } {
  const queryClient = useQueryClient()
  const [participants, setParticipants] = useState<Participant[]>([])
  const [connected, setConnected] = useState(false)
  // Kept in refs so the reconnect timer and the socket survive re-renders
  // without being torn down and rebuilt on every one.
  const socketRef = useRef<WebSocket | null>(null)
  const attemptRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!schoolId || !versionId) {
      setParticipants([])
      setConnected(false)
      return
    }

    let disposed = false

    async function open() {
      // A fresh token per attempt, not one captured once: a reconnect may
      // happen long after mount, by which point the original would have
      // expired and the server would (correctly) reject it.
      const token = await auth.currentUser?.getIdToken()
      if (!token || disposed) return

      const socket = new WebSocket(websocketUrl(versionId!, schoolId!))
      socketRef.current = socket

      socket.onopen = () => {
        // First frame must be the credential — the server accepts the
        // connection before authenticating it (a browser cannot set an
        // Authorization header on a WebSocket handshake, and a token in the
        // URL would leak into logs).
        socket.send(JSON.stringify({ token }))
        attemptRef.current = 0
        setConnected(true)
      }

      socket.onmessage = (event) => {
        let message: unknown
        try {
          message = JSON.parse(event.data as string)
        } catch {
          return // a frame we cannot parse is not worth acting on
        }
        if (typeof message !== 'object' || message === null) return
        const payload = message as { type?: string; participants?: Participant[]; actor?: string }

        if (payload.type === 'presence' && Array.isArray(payload.participants)) {
          setParticipants(payload.participants)
        } else if (payload.type === 'schedule-changed') {
          // Refetch rather than trusting the message to describe the change:
          // the server is the only authority on what the schedule now is.
          void queryClient.invalidateQueries({
            queryKey: ['schedule-assignments', schoolId, versionId],
          })
          void queryClient.invalidateQueries({
            queryKey: ['schedule-version', schoolId, versionId],
          })
          void queryClient.invalidateQueries({
            queryKey: ['schedule-violations', schoolId, versionId],
          })
          void queryClient.invalidateQueries({
            queryKey: ['schedule-analytics', schoolId, versionId],
          })
          if (payload.actor) {
            showToast({ type: 'info', message: `${payload.actor} changed this schedule.` })
          }
        }
      }

      socket.onclose = () => {
        setConnected(false)
        setParticipants([])
        if (disposed) return
        const delay = Math.min(RECONNECT_BASE_MS * 2 ** attemptRef.current, RECONNECT_MAX_MS)
        attemptRef.current += 1
        timerRef.current = setTimeout(() => void open(), delay)
      }

      // `onclose` fires after `onerror` in every case that matters here, so
      // reconnection is driven from there alone to avoid scheduling twice.
      socket.onerror = () => socket.close()
    }

    void open()

    return () => {
      disposed = true
      if (timerRef.current) clearTimeout(timerRef.current)
      // Detach the handler first: otherwise this deliberate close would
      // schedule a reconnect to a version the user has navigated away from.
      const socket = socketRef.current
      if (socket) {
        socket.onclose = null
        socket.close()
        socketRef.current = null
      }
      setConnected(false)
      setParticipants([])
    }
  }, [schoolId, versionId, queryClient])

  return { participants, connected }
}
