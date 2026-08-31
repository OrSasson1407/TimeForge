import {
  entriesForDay,
  formatTime,
  groupByWeekday,
  weekdayOf,
} from '../src/timetable/grouping'
import type { TimetableEntry, Weekday } from '../src/api/types'

function entry(
  weekday: Weekday,
  periodIndex: number,
  overrides: Partial<TimetableEntry> = {},
): TimetableEntry {
  return {
    assignment_id: `${weekday}-${periodIndex}`,
    day_id: `day_${weekday.toLowerCase()}`,
    weekday,
    time_period_id: `p${periodIndex}`,
    period_index: periodIndex,
    start_time: '08:00:00',
    end_time: '08:45:00',
    class_name: '7A',
    room_name: 'Room 1',
    subject_code: 'MATH',
    subject_name: 'Mathematics',
    ...overrides,
  }
}

describe('groupByWeekday', () => {
  it('orders days by the canonical week, not by input order', () => {
    const days = groupByWeekday([entry('WEDNESDAY', 1), entry('MONDAY', 1), entry('SUNDAY', 1)])

    expect(days.map((d) => d.weekday)).toEqual(['SUNDAY', 'MONDAY', 'WEDNESDAY'])
  })

  it('orders each day by period index', () => {
    const days = groupByWeekday([entry('MONDAY', 3), entry('MONDAY', 1), entry('MONDAY', 2)])

    expect(days[0].entries.map((e) => e.period_index)).toEqual([1, 2, 3])
  })

  it('omits days with no lessons rather than padding the week', () => {
    const days = groupByWeekday([entry('FRIDAY', 1)])

    expect(days).toHaveLength(1)
    expect(days[0].weekday).toBe('FRIDAY')
  })

  it('returns nothing for an empty timetable', () => {
    expect(groupByWeekday([])).toEqual([])
  })

  it('does not mutate the caller’s array', () => {
    const entries = [entry('MONDAY', 2), entry('MONDAY', 1)]
    const snapshot = entries.map((e) => e.period_index)

    groupByWeekday(entries)

    expect(entries.map((e) => e.period_index)).toEqual(snapshot)
  })
})

describe('formatTime', () => {
  it('drops the seconds', () => {
    expect(formatTime('08:00:00')).toBe('08:00')
    expect(formatTime('14:45:00')).toBe('14:45')
  })

  it('passes through anything it does not recognise rather than mangling it', () => {
    expect(formatTime('nonsense')).toBe('nonsense')
  })
})

describe('weekdayOf', () => {
  it('maps a Date onto the API vocabulary', () => {
    // 2026-08-31 is a Monday.
    expect(weekdayOf(new Date(2026, 7, 31))).toBe('MONDAY')
    expect(weekdayOf(new Date(2026, 7, 30))).toBe('SUNDAY')
  })
})

describe('entriesForDay', () => {
  it('returns just that day, in period order', () => {
    const result = entriesForDay(
      [entry('MONDAY', 2), entry('TUESDAY', 1), entry('MONDAY', 1)],
      'MONDAY',
    )

    expect(result.map((e) => e.period_index)).toEqual([1, 2])
  })

  it('returns an empty list for a day with nothing scheduled', () => {
    expect(entriesForDay([entry('MONDAY', 1)], 'FRIDAY')).toEqual([])
  })
})
