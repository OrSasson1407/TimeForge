import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ReportDisruptionPanel } from './ReportDisruptionPanel'
import { LanguageProvider } from '../../state/LanguageContext'
import type { ReportDisruptionRequest } from '../../types/rescheduling'

const mutate = vi.fn()

vi.mock('../../hooks/useRescheduling', () => ({
  useReportDisruption: () => ({
    mutate,
    isPending: false,
    isError: false,
    error: null,
    data: undefined,
  }),
}))

const days = [
  { id: 'day_mon', school_id: 's1', weekday: 'MONDAY' as const, is_active: true },
  { id: 'day_tue', school_id: 's1', weekday: 'TUESDAY' as const, is_active: true },
]
const periods = [
  {
    id: 'p1',
    school_id: 's1',
    index: 0,
    start_time: '08:00:00',
    end_time: '08:45:00',
    kind: 'LESSON' as const,
  },
]
const teachers = [
  {
    id: 't1',
    school_id: 's1',
    name: 'Dana',
    email: 'd@x.com',
    subject_ids: [],
    max_weekly_load: 30,
    max_consecutive: 4,
  },
]
const rooms = [
  {
    id: 'r1',
    school_id: 's1',
    name: 'Room 1',
    capacity: 30,
    room_type: 'STANDARD',
    capabilities: [],
    status: 'ACTIVE' as const,
  },
]

describe('ReportDisruptionPanel', () => {
  it('disables submit until a target, a slot, and a reason are all set', async () => {
    const user = userEvent.setup()
    render(
      <LanguageProvider>
        <ReportDisruptionPanel
          schoolId="s1"
          days={days}
          periods={periods}
          teachers={teachers}
          rooms={rooms}
          onRepaired={vi.fn()}
        />
      </LanguageProvider>,
    )

    const submit = screen.getByRole('button', { name: 'Report and repair' })
    expect(submit).toBeDisabled()

    await user.selectOptions(screen.getByLabelText('Teacher'), 't1')
    expect(submit).toBeDisabled() // still no slot or reason

    await user.click(screen.getByLabelText('MONDAY 08:00:00'))
    expect(submit).toBeDisabled() // still no reason

    await user.type(screen.getByLabelText('Reason'), 'Sick leave')
    expect(submit).toBeEnabled()
  })

  it('submits the selected teacher, slot, and reason', async () => {
    const user = userEvent.setup()
    render(
      <LanguageProvider>
        <ReportDisruptionPanel
          schoolId="s1"
          days={days}
          periods={periods}
          teachers={teachers}
          rooms={rooms}
          onRepaired={vi.fn()}
        />
      </LanguageProvider>,
    )

    await user.selectOptions(screen.getByLabelText('Teacher'), 't1')
    await user.click(screen.getByLabelText('MONDAY 08:00:00'))
    await user.type(screen.getByLabelText('Reason'), 'Sick leave')
    await user.click(screen.getByRole('button', { name: 'Report and repair' }))

    expect(mutate).toHaveBeenCalledTimes(1)
    const [body] = mutate.mock.calls[0] as [ReportDisruptionRequest, unknown]
    expect(body.event_type).toBe('TEACHER_UNAVAILABLE')
    expect(body.target_entity_id).toBe('t1')
    expect(body.affected_slots).toEqual([{ day_id: 'day_mon', time_period_id: 'p1' }])
    expect(body.reason).toBe('Sick leave')
  })

  it('switches target options to rooms when the event type changes', async () => {
    const user = userEvent.setup()
    render(
      <LanguageProvider>
        <ReportDisruptionPanel
          schoolId="s1"
          days={days}
          periods={periods}
          teachers={teachers}
          rooms={rooms}
          onRepaired={vi.fn()}
        />
      </LanguageProvider>,
    )

    await user.selectOptions(screen.getByLabelText('What became unavailable'), 'ROOM_UNAVAILABLE')

    expect(screen.getByLabelText('Room')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Room 1' })).toBeInTheDocument()
  })
})
