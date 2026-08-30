/**
 * Firebase Authentication wrapper. This is the ONLY module allowed to
 * import the Firebase SDK on the frontend, and it is used for identity
 * only — never for reading/writing business data (docs/01-CLAUDE.md rule 6,
 * docs/03-ARCHITECTURE.md #25).
 */
import { type Auth, connectAuthEmulator, getAuth } from 'firebase/auth'
import { initializeApp } from 'firebase/app'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

const firebaseApp = initializeApp(firebaseConfig)

export const auth: Auth = getAuth(firebaseApp)

if (import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true') {
  connectAuthEmulator(auth, 'http://localhost:9099', { disableWarnings: true })
}
