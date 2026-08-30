/**
 * Language state — English/Hebrew only (docs/02-PRD.md UX notes). Sets
 * <html lang>/<html dir> directly since RTL is a document-level concern,
 * not something CSS alone can retrofit onto a left-to-right layout.
 */
import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { LANGUAGES, translate } from '../i18n/translations'
import type { Language, TranslationKey } from '../i18n/translations'
import { safeStorage } from '../lib/safeStorage'

const STORAGE_KEY = 'timeforge.language'

function readStoredLanguage(): Language {
  const stored = safeStorage.get(STORAGE_KEY)
  return stored === 'he' ? 'he' : 'en'
}

interface LanguageContextValue {
  language: Language
  setLanguage: (language: Language) => void
  dir: 'ltr' | 'rtl'
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(readStoredLanguage)
  const dir = LANGUAGES.find((entry) => entry.code === language)?.dir ?? 'ltr'

  useEffect(() => {
    document.documentElement.lang = language
    document.documentElement.dir = dir
  }, [language, dir])

  function setLanguage(next: Language) {
    setLanguageState(next)
    safeStorage.set(STORAGE_KEY, next)
  }

  function t(key: TranslationKey, vars?: Record<string, string | number>) {
    return translate(key, language, vars)
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, dir, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext)
  if (!context) throw new Error('useLanguage must be used within a LanguageProvider')
  return context
}
