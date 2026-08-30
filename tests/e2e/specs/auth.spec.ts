import { expect, test } from '@playwright/test'

/**
 * The part of the demonstration scenario's "1. Login as administrator"
 * step (docs/03-ARCHITECTURE.md's Demonstration Scenario) that's testable
 * without a live Firebase project: an unauthenticated visitor is gated to
 * the login screen, and the form itself behaves correctly. Deeper
 * authenticated flows (steps 2-14) need a real or emulated Firebase Auth
 * project this environment doesn't have — see backend/README.md's
 * Firestore-emulator note for the equivalent, already-documented gap on
 * the backend side.
 */

test('an unauthenticated visitor is redirected to the login page', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  await expect(page).toHaveURL(/\/login$/)
})

test('the login form requires both an email and a password', async ({ page }) => {
  await page.goto('/login')

  const submit = page.getByRole('button', { name: 'Sign in' })
  await submit.click()

  // Native HTML5 `required` validation blocks submission — still on the
  // login page, no sign-in attempt was made.
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByLabel('Email')).toHaveJSProperty('validity.valid', false)
})

test('an invalid sign-in shows an error instead of navigating away', async ({ page }) => {
  await page.goto('/login')

  await page.getByLabel('Email').fill('nobody@example.com')
  await page.getByLabel('Password').fill('wrong-password')
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(page.getByRole('alert')).toBeVisible({ timeout: 15_000 })
  await expect(page).toHaveURL(/\/login$/)
})
