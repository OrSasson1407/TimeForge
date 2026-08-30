import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { EntityManager } from './EntityManager'
import type { EntityManagerConfig } from './EntityManager'

interface FakeEntity {
  id: string
  name: string
}
interface FakeUpsert {
  name: string
}

const config: EntityManagerConfig<FakeEntity, FakeUpsert> = {
  title: 'Widgets',
  fields: [{ key: 'name', label: 'Name', input: 'text' }],
  columns: [{ key: 'name', label: 'Name', render: (w) => w.name }],
  toFormState: (w) => ({ name: w.name }),
  emptyFormState: { name: '' },
  toUpsert: (form) => ({ name: form.name }),
}

describe('EntityManager', () => {
  it('creates a new entity with a caller-chosen id', async () => {
    const onSave = vi.fn()
    const user = userEvent.setup()
    render(
      <EntityManager
        config={config}
        entities={[]}
        isSaving={false}
        saveError={null}
        onSave={onSave}
      />,
    )

    await user.type(screen.getByLabelText('ID'), 'w1')
    await user.type(screen.getByLabelText('Name'), 'Widget One')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    expect(onSave).toHaveBeenCalledWith('w1', { name: 'Widget One' })
  })

  it('populates the form from an existing row on Edit, with the ID locked', async () => {
    const onSave = vi.fn()
    const user = userEvent.setup()
    render(
      <EntityManager
        config={config}
        entities={[{ id: 'w1', name: 'Widget One' }]}
        isSaving={false}
        saveError={null}
        onSave={onSave}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Edit' }))

    expect(screen.getByLabelText('ID')).toHaveValue('w1')
    expect(screen.getByLabelText('ID')).toBeDisabled()
    expect(screen.getByLabelText('Name')).toHaveValue('Widget One')

    await user.clear(screen.getByLabelText('Name'))
    await user.type(screen.getByLabelText('Name'), 'Renamed Widget')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    expect(onSave).toHaveBeenCalledWith('w1', { name: 'Renamed Widget' })
  })

  it('shows a save error', () => {
    render(
      <EntityManager
        config={config}
        entities={[]}
        isSaving={false}
        saveError="Something went wrong"
        onSave={vi.fn()}
      />,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong')
  })
})
