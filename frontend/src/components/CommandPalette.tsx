import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'

interface CommandEntry {
  label: string
  path: string
  adminOnly?: boolean
}

/** Cmd/Ctrl+K quick-jump — a natural extension of the single-letter
 * keyboard shortcuts (hooks/useKeyboardShortcuts.ts) for anyone who'd
 * rather type than memorize per-page keys. */
export function CommandPalette({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { t } = useLanguage()
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const entries = useMemo<CommandEntry[]>(
    () => [
      { label: t('nav.dashboard'), path: '/' },
      { label: t('nav.schedule'), path: '/schedule' },
      { label: t('nav.availability'), path: '/availability' },
      { label: t('nav.management'), path: '/management', adminOnly: true },
      { label: t('nav.constraints'), path: '/constraints', adminOnly: true },
      { label: t('nav.audit'), path: '/audit', adminOnly: true },
      { label: t('nav.pendingApprovals'), path: '/pending-approvals', adminOnly: true },
      { label: t('nav.manageUsers'), path: '/users', adminOnly: true },
      { label: t('nav.security'), path: '/security' },
    ],
    [t],
  )

  const visible = entries.filter((entry) => !entry.adminOnly || user?.role === 'ADMIN')
  const filtered = query.trim()
    ? visible.filter((entry) => entry.label.toLowerCase().includes(query.trim().toLowerCase()))
    : visible

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    setActiveIndex(0)
  }, [query])

  function go(entry: CommandEntry) {
    navigate(entry.path)
    onClose()
  }

  function handleKeyDown(event: React.KeyboardEvent) {
    if (event.key === 'Escape') {
      onClose()
    } else if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, filtered.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, 0))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      const entry = filtered[activeIndex]
      if (entry) go(entry)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal command-palette"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onClick={(event) => event.stopPropagation()}
      >
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Jump to a page…"
          aria-label="Jump to a page"
          className="command-palette-input"
        />
        <ul className="command-palette-list" role="listbox">
          {filtered.length === 0 && <li className="field-hint">No matches.</li>}
          {filtered.map((entry, index) => (
            <li key={entry.path}>
              <button
                type="button"
                role="option"
                aria-selected={index === activeIndex}
                className={
                  index === activeIndex ? 'command-palette-item active' : 'command-palette-item'
                }
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => go(entry)}
              >
                {entry.label}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
