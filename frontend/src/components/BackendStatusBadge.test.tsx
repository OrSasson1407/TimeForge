import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { BackendStatusBadge } from './BackendStatusBadge'
import { apiClient } from '../services/apiClient'

vi.mock('../services/apiClient', () => ({
  apiClient: { get: vi.fn() },
}))

describe('BackendStatusBadge', () => {
  it('shows the backend as online when the health check succeeds', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ status: 'ok' })

    render(<BackendStatusBadge />)

    await waitFor(() => expect(screen.getByTestId('api-status')).toHaveTextContent('online'))
  })

  it('shows the backend as offline when the health check fails', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('network error'))

    render(<BackendStatusBadge />)

    await waitFor(() => expect(screen.getByTestId('api-status')).toHaveTextContent('offline'))
  })
})
