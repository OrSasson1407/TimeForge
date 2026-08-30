import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  const tag = target.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable
}

/** Global single-key navigation shortcuts (GitHub/Gmail-style — no
 * modifier held, ignored while typing in a field). "?" opens the help
 * overlay listing all of them. */
export function useKeyboardShortcuts(onShowHelp: () => void) {
  const navigate = useNavigate()
  const { user } = useAuth()

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.metaKey || event.ctrlKey || event.altKey) return
      if (isTypingTarget(event.target)) return
      if (!user || user.role === 'PENDING') return

      switch (event.key) {
        case '?':
          event.preventDefault()
          onShowHelp()
          break
        case 'h':
          navigate('/')
          break
        case 's':
          navigate('/schedule')
          break
        case 'v':
          navigate('/availability')
          break
        case 'm':
          if (user.role === 'ADMIN') navigate('/management')
          break
        case 'u':
          if (user.role === 'ADMIN') navigate('/users')
          break
        default:
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [navigate, user, onShowHelp])
}
