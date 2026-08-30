import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, devices } from '@playwright/test'

const __dirname = dirname(fileURLToPath(import.meta.url))

/**
 * E2E tests for TimeForge's critical workflows (docs/02-PRD.md §15 and
 * docs/03-ARCHITECTURE.md's demonstration scenario) — not exhaustive path
 * coverage (docs/07-CODE_STANDARDS.md §22).
 */

// `uv run` is the documented, portable way to launch the backend (see
// ../../README.md), but it requires `uv` itself to be on PATH at test-run
// time. `uv sync` (the documented setup step) always leaves a working
// venv at backend/.venv regardless, so falling back to that venv's own
// `uvicorn` directly — the same interpreter `uv run` would have used —
// keeps this runnable in an environment where `uv` was used once for setup
// but isn't on PATH afterward, without weakening the primary command
// anywhere it IS on PATH (CI, a normal dev machine). Resolved to an
// absolute path: a bare relative `../../` path isn't reliably executable
// through cmd.exe's shell parsing on Windows.
const backendDir = resolve(__dirname, '../../backend')
const venvUvicorn = resolve(
  backendDir,
  process.platform === 'win32' ? '.venv/Scripts/uvicorn.exe' : '.venv/bin/uvicorn',
)
const backendCommand = existsSync(venvUvicorn)
  ? `"${venvUvicorn}" app.main:app --app-dir "${backendDir}" --port 8000`
  : `uv run --project "${backendDir}" uvicorn app.main:app --app-dir "${backendDir}" --port 8000`

export default defineConfig({
  testDir: './specs',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: backendCommand,
      url: 'http://localhost:8000/health',
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run dev --prefix ../../frontend',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
    },
  ],
})
