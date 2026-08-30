/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_FIREBASE_API_KEY: string
  readonly VITE_FIREBASE_AUTH_DOMAIN: string
  readonly VITE_FIREBASE_PROJECT_ID: string
  readonly VITE_FIREBASE_APP_ID: string
  readonly VITE_USE_FIREBASE_EMULATOR: string
  /** Public reCAPTCHA v2 site key (docs/06-TECH_STACK.md) — safe to expose
   * client-side by design, unlike the backend's paired secret key. Blank
   * means no real provider configured; RegisterPage shows a notice
   * instead of the widget. */
  readonly VITE_RECAPTCHA_SITE_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
