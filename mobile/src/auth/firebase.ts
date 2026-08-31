/**
 * Firebase Auth for React Native.
 *
 * `initializeAuth` with an explicit persistence, not `getAuth()`: on RN,
 * `getAuth()` defaults to in-memory persistence, which silently signs the
 * teacher out every time the OS reclaims the app — the single most
 * annoying possible bug in an app whose whole job is "glance at it between
 * lessons".
 *
 * Getting hold of `getReactNativePersistence` needs a note. `@firebase/auth`
 * ships it only from its `react-native` export condition, but the package's
 * export map lists a top-level `types` entry ahead of that condition, so
 * TypeScript always resolves the browser typings and never sees the
 * function. Metro, resolving at runtime, *does* take the `react-native`
 * condition, so the function is genuinely there when the app runs. Rather
 * than silence that mismatch with a blanket ts-ignore, the expected shape
 * is declared explicitly below and the absence is handled — so a future
 * Firebase release that moves or drops it degrades to a warning and
 * in-memory auth instead of a white screen.
 */

import AsyncStorage from '@react-native-async-storage/async-storage'
import { initializeApp, type FirebaseOptions } from 'firebase/app'
import * as firebaseAuth from 'firebase/auth'
import { getAuth, initializeAuth, type Auth, type Persistence } from 'firebase/auth'

import { firebaseConfig } from '../config'

type ReactNativePersistenceFactory = (storage: typeof AsyncStorage) => Persistence

const getReactNativePersistence = (
  firebaseAuth as unknown as {
    getReactNativePersistence?: ReactNativePersistenceFactory
  }
).getReactNativePersistence

let cachedAuth: Auth | null = null

export function getFirebaseAuth(): Auth {
  if (cachedAuth) return cachedAuth

  const app = initializeApp(firebaseConfig as FirebaseOptions)

  if (!getReactNativePersistence) {
    console.warn(
      'firebase/auth did not expose getReactNativePersistence — falling back to ' +
        'default persistence. Sessions may not survive an app restart.',
    )
    cachedAuth = getAuth(app)
    return cachedAuth
  }

  try {
    cachedAuth = initializeAuth(app, {
      persistence: getReactNativePersistence(AsyncStorage),
    })
  } catch {
    // initializeAuth throws if it has already run for this app — which
    // happens on a Fast Refresh in development, where the module is
    // re-evaluated but the native app instance is not. getAuth() returns
    // the already-initialized instance, persistence and all, instead of
    // crashing the reload.
    cachedAuth = getAuth(app)
  }
  return cachedAuth
}

/** The current user's ID token, or null when signed out. Always fetched
 * fresh rather than cached: Firebase rotates it hourly and handles the
 * refresh internally, so asking every time is both correct and cheap. */
export async function getIdToken(): Promise<string | null> {
  const user = getFirebaseAuth().currentUser
  if (!user) return null
  return user.getIdToken()
}
