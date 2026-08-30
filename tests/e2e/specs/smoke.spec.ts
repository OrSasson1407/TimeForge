import { expect, test } from '@playwright/test'

test('app shell loads and reaches the backend API', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'TimeForge' })).toBeVisible()
  await expect(page.getByTestId('api-status')).toHaveText('online')
})
