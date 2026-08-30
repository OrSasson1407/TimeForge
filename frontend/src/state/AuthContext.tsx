/**
 * Auth state, scoped to exactly that concern (docs/01-CLAUDE.md rule 11:
 * "State is separated by concern... no single global store holding
 * everything"). Combines two sources: Firebase's own auth state (identity)
 * and the backend's `/auth/me` (role/school_id/teacher_id) — the role is
 * always taken from the backend, never assumed from the Firebase user
 * alone (docs/03-ARCHITECTURE.md #23-24: the backend is the sole
 * authorization authority).
 */
import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import {
  GoogleAuthProvider,
  onAuthStateChanged,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
} from 'firebase/auth'
import type { User as FirebaseUser } from 'firebase/auth'
import { auth } from '../services/firebaseAuth'
import { authApi } from '../services/authApi'
import { ApiError } from '../services/apiClient'
import type { User } from '../types/auth'

interface OAuthProfile {
  displayName: string | null
  email: string | null
}

interface AuthContextValue {
  /** The backend's own User record (role, school_id, teacher_id) — null
   * while loading, or when signed out, or when a verified Firebase
   * identity has no matching TimeForge user record. */
  user: User | null
  loading: boolean
  error: string | null
  /** True when Firebase has a signed-in identity (e.g. a first-time Google
   * sign-in) but no TimeForge User record exists for it yet — the
   * frontend should show CompleteProfilePage rather than treating this as
   * an error. See the heuristic note in the effect below for why a bare
   * 401 from /auth/me is trusted as "needs onboarding" here. */
  needsOnboarding: boolean
  /** display_name/email from the Firebase identity itself, for
   * pre-filling the onboarding form — only meaningful while
   * needsOnboarding is true. */
  oauthProfile: OAuthProfile | null
  signIn: (email: string, password: string) => Promise<void>
  signInWithGoogle: () => Promise<void>
  sendPasswordReset: (email: string) => Promise<void>
  signOut: () => Promise<void>
  /** Re-checks /auth/me — call after completing onboarding so the newly
   * created (PENDING) User record is picked up without a full reload. */
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [needsOnboarding, setNeedsOnboarding] = useState(false)
  const [oauthProfile, setOauthProfile] = useState<OAuthProfile | null>(null)

  // Accepts the Firebase user explicitly rather than always reading
  // `auth.currentUser` — the onAuthStateChanged listener below already has
  // it as a parameter, and using that directly (rather than re-reading a
  // module-level mutable field) doesn't depend on Firebase's internal
  // ordering guarantee that `auth.currentUser` is updated before listeners
  // fire. `refreshUser` (called with no argument, from outside the
  // listener) is the one legitimate case that still needs the live value.
  async function resolveCurrentUser(firebaseUser: FirebaseUser | null = auth.currentUser) {
    if (!firebaseUser) {
      setUser(null)
      setNeedsOnboarding(false)
      setOauthProfile(null)
      return
    }
    try {
      const resolved = await authApi.me()
      setUser(resolved)
      setNeedsOnboarding(false)
      setError(null)
    } catch (err) {
      setUser(null)
      // A signed-in Firebase identity implies the ID token itself is
      // fresh/valid — the only realistic reason /auth/me then returns 401
      // is "no TimeForge User record for this uid" (see
      // backend/app/infrastructure/firebase/auth.py's resolve_user), which
      // means this is a first-time OAuth sign-in that still needs
      // CompleteProfilePage, not a real error.
      if (err instanceof ApiError && err.status === 401) {
        setNeedsOnboarding(true)
        setOauthProfile({
          displayName: firebaseUser.displayName,
          email: firebaseUser.email,
        })
        setError(null)
      } else {
        setNeedsOnboarding(false)
        setError('Signed in with Firebase, but no matching TimeForge account was found.')
      }
    }
  }

  useEffect(() => {
    return onAuthStateChanged(auth, (firebaseUser) => {
      if (!firebaseUser) {
        setUser(null)
        setNeedsOnboarding(false)
        setOauthProfile(null)
        setLoading(false)
        return
      }
      setLoading(true)
      void resolveCurrentUser(firebaseUser).finally(() => setLoading(false))
    })
  }, [])

  async function signIn(email: string, password: string) {
    setError(null)
    try {
      await signInWithEmailAndPassword(auth, email, password)
    } catch {
      setError('Invalid email or password.')
      throw new Error('sign-in failed')
    }
  }

  async function signInWithGoogle() {
    setError(null)
    try {
      await signInWithPopup(auth, new GoogleAuthProvider())
    } catch {
      setError('Google sign-in failed or was cancelled.')
      throw new Error('google sign-in failed')
    }
  }

  async function sendPasswordReset(email: string) {
    await sendPasswordResetEmail(auth, email)
  }

  async function signOut() {
    await firebaseSignOut(auth)
    setUser(null)
    setNeedsOnboarding(false)
    setOauthProfile(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        needsOnboarding,
        oauthProfile,
        signIn,
        signInWithGoogle,
        sendPasswordReset,
        signOut,
        refreshUser: resolveCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within an AuthProvider')
  return context
}
