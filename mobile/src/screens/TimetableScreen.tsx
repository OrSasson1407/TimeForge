import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native'
import { signOut } from 'firebase/auth'

import type { ApiClient } from '../api/client'
import type { MyTimetable, Weekday } from '../api/types'
import { getFirebaseAuth } from '../auth/firebase'
import type { TimetableCache } from '../storage/timetableCache'
import { formatTime, groupByWeekday, weekdayOf } from '../timetable/grouping'

interface Props {
  api: ApiClient
  cache: TimetableCache
  userId: string
  schoolId: string
  displayName: string
}

type Mode = 'today' | 'week'

export function TimetableScreen({ api, cache, userId, schoolId, displayName }: Props) {
  const [timetable, setTimetable] = useState<MyTimetable | null>(null)
  const [cachedAt, setCachedAt] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>('today')

  const today: Weekday = useMemo(() => weekdayOf(new Date()), [])

  const refresh = useCallback(
    async (isPullToRefresh: boolean) => {
      if (isPullToRefresh) setRefreshing(true)
      try {
        const fresh = await api.myTimetable(schoolId)
        setTimetable(fresh)
        setCachedAt(null)
        setError(null)
        await cache.write(userId, fresh)
      } catch {
        // Offline-first: a failed refresh is only an error if there is
        // nothing cached to fall back on. Otherwise the teacher keeps
        // seeing a timetable that is almost certainly still correct.
        setError('Could not refresh. Showing your saved timetable.')
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [api, cache, schoolId, userId],
  )

  useEffect(() => {
    let cancelled = false

    async function load() {
      // Paint from cache first so the screen is useful immediately, then
      // refresh behind it. On a corridor with no signal, step one is the
      // whole experience.
      const cached = await cache.read(userId)
      if (!cancelled && cached) {
        setTimetable(cached.timetable)
        setCachedAt(cached.cachedAt)
        setLoading(false)
      }
      if (!cancelled) await refresh(false)
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [cache, refresh, userId])

  const days = useMemo(() => groupByWeekday(timetable?.entries ?? []), [timetable])
  const visibleDays = mode === 'today' ? days.filter((d) => d.weekday === today) : days

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4338ca" />
      </View>
    )
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>My timetable</Text>
          <Text style={styles.subtitle}>{displayName}</Text>
        </View>
        <TouchableOpacity
          onPress={() => void signOut(getFirebaseAuth())}
          accessibilityRole="button"
          accessibilityLabel="Sign out"
        >
          <Text style={styles.signOut}>Sign out</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.tabs}>
        {(['today', 'week'] as Mode[]).map((value) => (
          <TouchableOpacity
            key={value}
            style={[styles.tab, mode === value && styles.tabActive]}
            onPress={() => setMode(value)}
            accessibilityRole="button"
            accessibilityState={{ selected: mode === value }}
          >
            <Text style={[styles.tabText, mode === value && styles.tabTextActive]}>
              {value === 'today' ? 'Today' : 'Full week'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {error ? <Text style={styles.warning}>{error}</Text> : null}
      {cachedAt ? (
        <Text style={styles.stale}>
          Saved copy from {new Date(cachedAt).toLocaleString()}
        </Text>
      ) : null}

      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => void refresh(true)} />
        }
      >
        {timetable?.version_id === null ? (
          <Text style={styles.empty}>No timetable has been published yet.</Text>
        ) : visibleDays.length === 0 ? (
          <Text style={styles.empty}>
            {mode === 'today' ? 'Nothing scheduled today.' : 'You have no scheduled lessons.'}
          </Text>
        ) : (
          visibleDays.map((day) => (
            <View key={day.weekday} style={styles.day}>
              <Text style={styles.dayName}>{day.weekday}</Text>
              {day.entries.map((entry) => (
                <View key={entry.assignment_id} style={styles.lesson}>
                  <Text style={styles.lessonTime}>
                    {formatTime(entry.start_time)}–{formatTime(entry.end_time)}
                  </Text>
                  <View style={styles.lessonBody}>
                    <Text style={styles.lessonSubject}>{entry.subject_name}</Text>
                    <Text style={styles.lessonMeta}>
                      {entry.class_name} · {entry.room_name}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          ))
        )}
      </ScrollView>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f7f7f8', paddingTop: 56 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f7f7f8' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 12,
  },
  title: { fontSize: 24, fontWeight: '700', color: '#1f1f28' },
  subtitle: { fontSize: 13, color: '#6b6b76', marginTop: 2 },
  signOut: { color: '#4338ca', fontWeight: '600' },
  tabs: { flexDirection: 'row', paddingHorizontal: 20, gap: 8, paddingBottom: 8 },
  tab: { paddingVertical: 8, paddingHorizontal: 16, borderWidth: 1, borderColor: '#d8d8de' },
  tabActive: { backgroundColor: '#4338ca', borderColor: '#4338ca' },
  tabText: { color: '#1f1f28', fontSize: 14 },
  tabTextActive: { color: '#fff', fontWeight: '600' },
  warning: { color: '#d97706', paddingHorizontal: 20, paddingVertical: 4, fontSize: 13 },
  stale: { color: '#6b6b76', paddingHorizontal: 20, fontSize: 12 },
  scroll: { padding: 20, paddingBottom: 48 },
  empty: { color: '#6b6b76', fontSize: 15, textAlign: 'center', marginTop: 48 },
  day: { marginBottom: 24 },
  dayName: { fontSize: 12, letterSpacing: 1, color: '#6b6b76', marginBottom: 8 },
  lesson: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e3e3e6',
    padding: 14,
    marginBottom: 8,
  },
  lessonTime: { width: 104, color: '#4338ca', fontWeight: '600', fontSize: 14 },
  lessonBody: { flex: 1 },
  lessonSubject: { fontSize: 16, fontWeight: '600', color: '#1f1f28' },
  lessonMeta: { fontSize: 13, color: '#6b6b76', marginTop: 2 },
})
