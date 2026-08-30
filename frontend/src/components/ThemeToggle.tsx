import { useTheme } from '../state/ThemeContext'
import type { Theme } from '../state/ThemeContext'

const ORDER: Theme[] = ['system', 'light', 'dark']
const LABEL: Record<Theme, string> = { system: 'System', light: 'Light', dark: 'Dark' }
const ICON: Record<Theme, string> = { system: '🖥', light: '☀', dark: '☾' }

/** Cycles System -> Light -> Dark -> System. A single button rather than a
 * 3-way switch to keep the header compact; the icon+label makes the
 * current state legible without extra chrome. */
export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  function cycle() {
    const next = ORDER[(ORDER.indexOf(theme) + 1) % ORDER.length]
    setTheme(next)
  }

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={cycle}
      aria-label={`Theme: ${LABEL[theme]}. Click to change.`}
      title={`Theme: ${LABEL[theme]}`}
    >
      <span aria-hidden="true">{ICON[theme]}</span> {LABEL[theme]}
    </button>
  )
}
