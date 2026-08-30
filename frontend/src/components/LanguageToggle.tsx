import { LANGUAGES } from '../i18n/translations'
import { useLanguage } from '../state/LanguageContext'

/** EN/HE switcher — two languages only, so a toggle beats a dropdown. */
export function LanguageToggle() {
  const { language, setLanguage } = useLanguage()

  return (
    <div className="language-toggle" role="group" aria-label="Language">
      {LANGUAGES.map((entry) => (
        <button
          key={entry.code}
          type="button"
          className={entry.code === language ? 'language-option active' : 'language-option'}
          onClick={() => setLanguage(entry.code)}
          aria-pressed={entry.code === language}
        >
          {entry.label}
        </button>
      ))}
    </div>
  )
}
