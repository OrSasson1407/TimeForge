/**
 * Push registration.
 *
 * Two things this deliberately does NOT do: ask for permission before the
 * user has signed in (an OS permission prompt on a launch screen, before
 * the app has shown its value, is the classic way to get denied
 * permanently), and treat a denial as an error (a teacher who does not want
 * notifications still wants their timetable).
 */

import * as Device from 'expo-device'
import * as Notifications from 'expo-notifications'
import { Platform } from 'react-native'

import type { ApiClient } from '../api/client'

export type PushPlatform = 'IOS' | 'ANDROID'

function currentPlatform(): PushPlatform | null {
  if (Platform.OS === 'ios') return 'IOS'
  if (Platform.OS === 'android') return 'ANDROID'
  return null // web/desktop preview — nothing to register
}

/**
 * Returns the registered token, or null if registration did not happen for
 * any reason (simulator, denied permission, unsupported platform). Never
 * throws: a failure here must not stop the app from showing a timetable.
 */
export async function registerForPush(api: ApiClient): Promise<string | null> {
  try {
    // A simulator cannot receive a real push token, and asking for one
    // throws rather than returning null.
    if (!Device.isDevice) return null

    const platform = currentPlatform()
    if (!platform) return null

    const existing = await Notifications.getPermissionsAsync()
    let granted = existing.granted
    if (!granted && existing.canAskAgain) {
      granted = (await Notifications.requestPermissionsAsync()).granted
    }
    if (!granted) return null

    const { data: token } = await Notifications.getDevicePushTokenAsync()
    if (typeof token !== 'string' || !token) return null

    await api.registerDevice(token, platform)
    return token
  } catch (error) {
    console.warn('Push registration skipped:', error)
    return null
  }
}

/** Called on sign-out so a shared device stops receiving a former user's
 * school announcements. Best-effort, same reasoning as above. */
export async function unregisterFromPush(api: ApiClient, token: string): Promise<void> {
  try {
    await api.unregisterDevice(token)
  } catch (error) {
    console.warn('Push unregistration failed:', error)
  }
}
