# TimeForge Frontend

React + TypeScript + Vite single-page app. See [../docs](../docs) — this package implements [03-ARCHITECTURE.md](../docs/03-ARCHITECTURE.md) §8.

## Setup

```bash
npm install
cp ../.env.example ../.env   # then fill in real VITE_FIREBASE_* values
```

The `VITE_FIREBASE_*` variables are required, not optional: Firebase Auth's SDK validates `VITE_FIREBASE_API_KEY` at `getAuth()` call time (`src/services/firebaseAuth.ts`), before the app renders anything — with it unset, the app fails to load at all (a blank page, plus an `auth/invalid-api-key` error in the browser console), rather than rendering degraded. This was found and confirmed while manually verifying Phase 8 in a browser.

## Run the dev server

```bash
npm run dev
```

## Test

```bash
npm run test
```

## Lint, format, type-check

```bash
npm run lint
npm run format:check
npm run typecheck
```
