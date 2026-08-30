/**
 * Explicit Light/Dark/System theme choice, layered on top of the
 * `prefers-color-scheme` CSS already in index.css. "System" removes the
 * override entirely and lets the OS preference win; "light"/"dark" stamp
 * a `data-theme` attribute on <html> that index.css's `:root[data-theme]`
 * rules take priority over the media query for.
 */
import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { safeStorage } from '../lib/safeStorage'

export type Theme = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'timeforge.theme'

function readStoredTheme(): Theme {
  const stored = safeStorage.get(STORAGE_KEY)
  return stored === 'light' || stored === 'dark' ? stored : 'system'
}

interface ThemeContextValue {
  theme: Theme
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(readStoredTheme)

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'system') {
      root.removeAttribute('data-theme')
    } else {
      root.setAttribute('data-theme', theme)
    }
  }, [theme])

  function setTheme(next: Theme) {
    setThemeState(next)
    if (next === 'system') {
      safeStorage.remove(STORAGE_KEY)
    } else {
      safeStorage.set(STORAGE_KEY, next)
    }
  }

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within a ThemeProvider')
  return context
}
