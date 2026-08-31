# TimeForge Mobile

An Expo/React Native companion app for **teachers**: sign in, see your own
published timetable, and get a push notification when a new one is
published.

## What is and is not verified

Be aware of this before trusting any of it in front of a class.

**Verified here (runs in Node, no device needed):**

- `npm run typecheck` — the whole app, screens included, compiles clean.
- `npm test` — 24 unit tests over the pure logic: week grouping and
  ordering, time formatting, the offline cache (per-user isolation, corrupt
  and stale-shape reads, a store that refuses to write), and the API client
  (bearer header, URL encoding, backend error messages, error typing).

**NOT verified here:** anything that needs a simulator or a handset —
whether the screens actually lay out correctly, whether Firebase Auth
persists a session across a real app restart, and whether push tokens are
issued and notifications arrive. None of that can be exercised without an
Android SDK / Xcode, which this codebase was built without. Treat the UI
and the push path as **written but untested** until someone runs it on a
device.

The one place that gap is most likely to bite is
`src/auth/firebase.ts`: `getReactNativePersistence` is resolvable by Metro
at runtime but not by TypeScript (Firebase's export map lists `types`
ahead of its `react-native` condition). That is handled explicitly with a
declared type and a runtime fallback rather than a blanket `ts-ignore`, but
it is the first thing to check if sessions do not survive a restart.

## Scope: teachers only

The original ask mentioned students. There is currently **no STUDENT role**
in the domain (`UserRole` is ADMIN / TEACHER / PENDING) and no
student-to-class relationship, so a student view is not buildable without
new domain modelling — a new role, a student entity, enrolment, and the
authorization rules that go with them. That is a backend change, not a
mobile one.

## Setup

```bash
cd mobile
npm install
```

Then fill in `app.json`'s `expo.extra`:

- `apiBaseUrl` — your deployed backend. Note that `localhost` refers to the
  *device*, so a physical handset needs your machine's LAN address (e.g.
  `http://192.168.1.20:8000`), not `http://localhost:8000`.
- `firebase` — the same web config values the frontend uses.

## Run

```bash
npm start          # Expo dev server; open in Expo Go or a dev build
npm run android
npm run ios
```

Push notifications need a **development build or a real device** — Expo Go
cannot receive them, and a simulator has no push token at all.
`registerForPush` detects this and skips registration rather than failing,
so the timetable still works.

## Design notes

- **Offline-first.** The timetable screen paints from the AsyncStorage
  cache immediately, then refreshes behind it. A failed refresh with a
  cached copy present is a warning, not an error — the timetable changes a
  few times a term, so a saved copy is nearly always still correct, and a
  corridor with no signal is the normal case, not the exceptional one.
- **One denormalized request.** `GET /schedules/my-timetable` returns
  names, not ids, so the phone needs exactly one round trip and can render
  entirely from cache. It is also scoped server-side to the caller's own
  `teacher_id`, so it cannot be used to read a colleague's schedule.
- **Push on publish only.** Draft edits do not notify; see
  `NotifySchedulePublishedUseCase` on the backend for why.
- **Permission asked after sign-in**, never on the launch screen — a prompt
  before the app has shown any value is the reliable way to get denied
  permanently.
