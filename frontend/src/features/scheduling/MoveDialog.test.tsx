import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MoveDialog } from './MoveDialog'
import { LanguageProvider } from '../../state/LanguageContext'
import type {
  ProposedMove,
  ScheduleAssignment,
  ScheduleVersion,
  ValidateMoveResponse,
} from '../../types/schedule'

// MoveDialog reaches scheduleApi -> apiClient -> firebaseAuth, and that
// module calls getAuth() at import time, which throws
// `auth/invalid-api-key` wherever VITE_FIREBASE_* is unset — as it is in
// CI. Nothing in this file exercises Firebase, so the one module that needs
// credentials is stubbed, matching App.test.tsx.
vi.mock('../../services/firebaseAuth', () => ({ auth: { currentUser: null } }))

const applyMutate = vi.fn()

vi.mock('../../hooks/useSchedule', () => ({
  useValidateMove: () => {
    const [data, setData] = useState<ValidateMoveResponse | undefined>(undefined)
    return {
      data,
      isPending: false,
      mutate: (move: ProposedMove) => {
        setData(
          move.teacher_id === 't_blocked'
            ? { result: 'INVALID', message: 'Teacher conflict', violation: null }
            : { result: 'VALID', message: null, violation: null },
        )
      },
    }
  },
  useApplyMove: () => ({
    mutate: applyMutate,
    isPending: false,
    isError: false,
    error: null,
  }),
}))

const version: ScheduleVersion = {
  id: 'v1',
  schedule_id: 's1',
  status: 'DRAFT',
  created_by: 'admin_1',
  created_at: '2026-01-01T00:00:00Z',
  parent_version_id: null,
  score: { hard_violations: 0, soft_penalty: 0, quality: 90 },
  reason: null,
  assignment_count: 1,
  version_tag: 0,
}

const assignment: ScheduleAssignment = {
  id: 'a1',
  version_id: 'v1',
  lesson_id: 'req1_1',
  teacher_id: 't1',
  class_id: 'c1',
  room_id: 'r1',
  time_period_id: 'p1',
  day_id: 'day_mon',
}

const days = [{ id: 'day_mon', school_id: 's1', weekday: 'MONDAY' as const, is_active: true }]
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
    email: 'dana@x.com',
    subject_ids: [],
    max_weekly_load: 30,
    max_consecutive: 4,
  },
  {
    id: 't_blocked',
    school_id: 's1',
    name: 'Blocked Teacher',
    email: 'b@x.com',
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

describe('MoveDialog', () => {
  it('disables Apply until a successful Validate for the exact current form', async () => {
    const user = userEvent.setup()
    render(
      <LanguageProvider>
        <MoveDialog
          schoolId="s1"
          version={version}
          assignment={assignment}
          days={days}
          periods={periods}
          teachers={teachers}
          rooms={rooms}
          onClose={vi.fn()}
        />
      </LanguageProvider>,
    )

    expect(screen.getByRole('button', { name: 'Apply' })).toBeDisabled()

    await user.click(screen.getByRole('button', { name: 'Validate' }))
    expect(await screen.findByText('VALID')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Apply' })).toBeEnabled()

    await user.click(screen.getByRole('button', { name: 'Apply' }))
    expect(applyMutate).toHaveBeenCalledWith(
      expect.objectContaining({ assignment_id: 'a1', teacher_id: 't1', expected_version_tag: 0 }),
      expect.anything(),
    )
  })

  it('re-locks Apply after the form changes past validation', async () => {
    const user = userEvent.setup()
    render(
      <LanguageProvider>
        <MoveDialog
          schoolId="s1"
          version={version}
          assignment={assignment}
          days={days}
          periods={periods}
          teachers={teachers}
          rooms={rooms}
          onClose={vi.fn()}
        />
      </LanguageProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Validate' }))
    expect(screen.getByRole('button', { name: 'Apply' })).toBeEnabled()

    await user.selectOptions(screen.getByLabelText('Room'), 'r1') // no-op change still re-selects same value
    await user.selectOptions(screen.getByLabelText('Teacher'), 't_blocked')

    expect(screen.getByRole('button', { name: 'Apply' })).toBeDisabled()
  })

  it('never enables Apply when validation reports INVALID', async () => {
    const user = userEvent.setup()
    render(
      <LanguageProvider>
        <MoveDialog
          schoolId="s1"
          version={version}
          assignment={assignment}
          days={days}
          periods={periods}
          teachers={teachers}
          rooms={rooms}
          onClose={vi.fn()}
        />
      </LanguageProvider>,
    )

    await user.selectOptions(screen.getByLabelText('Teacher'), 't_blocked')
    await user.click(screen.getByRole('button', { name: 'Validate' }))

    expect(await screen.findByText(/INVALID/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Apply' })).toBeDisabled()
  })
})
