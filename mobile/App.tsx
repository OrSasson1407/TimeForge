import { useEffect, useMemo, useRef, useState } from 'react'
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native'
import { StatusBar } from 'expo-status-bar'
import AsyncStorage from '@react-native-async-storage/async-storage'
import { onAuthStateChanged, type User as FirebaseUser } from 'firebase/auth'

import { createApiClient } from './src/api/client'
import type { CurrentUser } from './src/api/types'
import { getFirebaseAuth, getIdToken } from './src/auth/firebase'
import { apiBaseUrl } from './src/config'
import { registerForPush, unregisterFromPush } from './src/notifications/registerForPush'
import { SignInScreen } from './src/screens/SignInScreen'
import { TimetableScreen } from './src/screens/TimetableScreen'
import { createTimetableCache } from './src/storage/timetableCache'

export default function App() {
  // Built once: recreating the client on every render would give the
  // timetable screen a new object identity each time and re-trigger its
  // load effect forever.
  const api = useMemo(
    () => createApiClient({ baseUrl: apiBaseUrl, getToken: getIdToken }),
    [],
  )
  const cache = useMemo(() => createTimetableCache(AsyncStorage), [])

  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null)
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [resolving, setResolving] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // Held so sign-out can unregister the exact token this session registered.
  const pushTokenRef = useRef<string | null>(null)

  useEffect(() => onAuthStateChanged(getFirebaseAuth(), setFirebaseUser), [])

  useEffect(() => {
    let cancelled = false

    async function resolve() {
      if (!firebaseUser) {
        // Signed out. Drop the push registration first so a shared device
        // stops receiving this teacher's school announcements.
        const token = pushTokenRef.current
        if (token) {
          pushTokenRef.current = null
          await unregisterFromPush(api, token)
        }
        if (!cancelled) {
          setUser(null)
          setError(null)
          setResolving(false)
        }
        return
      }

      setResolving(true)
      try {
        // The role and school always come from the backend, never from the
        // Firebase identity — same rule the web app follows.
        const resolved = await api.me()
        if (cancelled) return
        setUser(resolved)
        setError(null)
        pushTokenRef.current = await registerForPush(api)
      } catch {
        if (!cancelled) {
          setUser(null)
          setError('This account has no TimeForge access yet.')
        }
      } finally {
        if (!cancelled) setResolving(false)
      }
    }

    void resolve()
    return () => {
      cancelled = true
    }
  }, [api, firebaseUser])

  if (resolving) {
    return (
      <View style={styles.centered}>
        <StatusBar style="auto" />
        <ActivityIndicator size="large" color="#4338ca" />
      </View>
    )
  }

  if (!firebaseUser || !user) {
    return (
      <>
        <StatusBar style="auto" />
        {error ? <Text style={styles.banner}>{error}</Text> : null}
        <SignInScreen />
      </>
    )
  }

  // A PENDING account has authenticated but has not been approved, and an
  // account with no linked teacher record has no timetable to show. Both
  // are ordinary states with a plain explanation, not errors.
  if (user.role === 'PENDING' || !user.teacher_id) {
    return (
      <View style={styles.centered}>
        <StatusBar style="auto" />
        <Text style={styles.noticeTitle}>Nothing to show yet</Text>
        <Text style={styles.notice}>
          {user.role === 'PENDING'
            ? 'An administrator still needs to approve your account.'
            : 'Your account is not linked to a teacher record, so it has no timetable.'}
        </Text>
      </View>
    )
  }

  return (
    <>
      <StatusBar style="auto" />
      <TimetableScreen
        api={api}
        cache={cache}
        userId={user.id}
        schoolId={user.school_id}
        displayName={user.display_name}
      />
    </>
  )
}

const styles = StyleSheet.create({
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f7f7f8',
    padding: 32,
  },
  banner: { backgroundColor: '#fef2f2', color: '#dc2626', padding: 12, textAlign: 'center' },
  noticeTitle: { fontSize: 20, fontWeight: '700', color: '#1f1f28', marginBottom: 8 },
  notice: { fontSize: 15, color: '#6b6b76', textAlign: 'center', lineHeight: 22 },
})
