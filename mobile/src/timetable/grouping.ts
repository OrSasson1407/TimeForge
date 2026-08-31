/** Pure timetable shaping — no React, no network, no storage, so it is
 * fully unit-testable in Node without a simulator. Everything the screen
 * needs to decide *what* to draw lives here; the screen only draws it. */

import type { TimetableEntry, Weekday } from '../api/types'

/** Canonical week order. Not derived from the data: a school whose week
 * runs Sunday-Thursday (as many do) still has its days in this order, and
 * sorting by the day_id string would produce an arbitrary one. */
export const WEEKDAY_ORDER: Weekday[] = [
  'SUNDAY',
  'MONDAY',
  'TUESDAY',
  'WEDNESDAY',
  'THURSDAY',
  'FRIDAY',
  'SATURDAY',
]

export interface DaySchedule {
  weekday: Weekday
  entries: TimetableEntry[]
}

/**
 * Group into days, in week order, with each day's lessons in period order.
 *
 * Days with no lessons are omitted entirely rather than included empty: on
 * a phone screen a run of blank days is just scrolling between the things
 * the teacher actually came to look at.
 */
export function groupByWeekday(entries: TimetableEntry[]): DaySchedule[] {
  const byDay = new Map<Weekday, TimetableEntry[]>()
  for (const entry of entries) {
    const existing = byDay.get(entry.weekday)
    if (existing) existing.push(entry)
    else byDay.set(entry.weekday, [entry])
  }

  const days: DaySchedule[] = []
  for (const weekday of WEEKDAY_ORDER) {
    const dayEntries = byDay.get(weekday)
    if (!dayEntries) continue
    days.push({
      weekday,
      entries: [...dayEntries].sort((a, b) => a.period_index - b.period_index),
    })
  }
  return days
}

/** "08:00:00" -> "08:00". The seconds are always zero in practice and cost
 * width that a phone does not have to spare. */
export function formatTime(value: string): string {
  const [hours, minutes] = value.split(':')
  if (hours === undefined || minutes === undefined) return value
  return `${hours}:${minutes}`
}

/** The weekday a JS Date falls on, in the same vocabulary the API uses.
 * `Date.getDay()` is 0=Sunday, which is exactly WEEKDAY_ORDER's index. */
export function weekdayOf(date: Date): Weekday {
  return WEEKDAY_ORDER[date.getDay()]
}

/**
 * The lessons for one specific day, or an empty list. Used for the "today"
 * view the app opens on — a teacher checking their phone between classes
 * wants today, not the whole week.
 */
export function entriesForDay(entries: TimetableEntry[], weekday: Weekday): TimetableEntry[] {
  return groupByWeekday(entries).find((day) => day.weekday === weekday)?.entries ?? []
}
