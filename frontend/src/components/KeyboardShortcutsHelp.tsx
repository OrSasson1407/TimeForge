import { useEffect, useRef } from 'react'
import { useLanguage } from '../state/LanguageContext'

const SHORTCUTS: {
  key: string
  labelKey:
    | 'shortcuts.home'
    | 'shortcuts.schedule'
    | 'shortcuts.availability'
    | 'shortcuts.management'
    | 'shortcuts.users'
    | 'shortcuts.help'
    | 'shortcuts.palette'
}[] = [
  { key: 'h', labelKey: 'shortcuts.home' },
  { key: 's', labelKey: 'shortcuts.schedule' },
  { key: 'v', labelKey: 'shortcuts.availability' },
  { key: 'm', labelKey: 'shortcuts.management' },
  { key: 'u', labelKey: 'shortcuts.users' },
  { key: 'Ctrl/⌘ K', labelKey: 'shortcuts.palette' },
  { key: '?', labelKey: 'shortcuts.help' },
]

export function KeyboardShortcutsHelp({ onClose }: { onClose: () => void }) {
  const { t } = useLanguage()
  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    dialogRef.current?.focus()
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        ref={dialogRef}
        className="modal shortcuts-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="shortcuts-title"
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="shortcuts-title">{t('shortcuts.title')}</h2>
          <button
            type="button"
            className="btn-link"
            onClick={onClose}
            aria-label={t('common.close')}
          >
            ×
          </button>
        </div>
        <p className="field-hint">{t('shortcuts.hint')}</p>
        <dl className="shortcuts-list">
          {SHORTCUTS.map((shortcut) => (
            <div key={shortcut.key} className="shortcuts-row">
              <dt>
                <kbd>{shortcut.key}</kbd>
              </dt>
              <dd>{t(shortcut.labelKey)}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  )
}
