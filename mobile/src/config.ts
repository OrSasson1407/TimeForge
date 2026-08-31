/** Runtime configuration, from `app.json`'s `expo.extra`. Read through
 * expo-constants rather than a bundler define so the same JS bundle can be
 * pointed at staging or production without a rebuild. */

import Constants from 'expo-constants'

interface Extra {
  apiBaseUrl: string
  firebase: {
    apiKey: string
    authDomain: string
    projectId: string
    appId: string
  }
}

const extra = (Constants.expoConfig?.extra ?? {}) as Partial<Extra>

if (!extra.apiBaseUrl) {
  // Fail loudly at startup rather than producing a stream of confusing
  // network errors against `undefined/schedules/...` later.
  throw new Error('Missing expo.extra.apiBaseUrl — see mobile/app.json')
}

export const apiBaseUrl: string = extra.apiBaseUrl
export const firebaseConfig = extra.firebase ?? {
  apiKey: '',
  authDomain: '',
  projectId: '',
  appId: '',
}
