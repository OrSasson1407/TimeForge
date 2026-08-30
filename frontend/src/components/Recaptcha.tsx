import { useEffect, useRef } from 'react'

/** Minimal wrapper around Google's reCAPTCHA v2 (checkbox) widget, loaded
 * with `render=explicit` so it only mounts where/when this component does
 * — no global auto-render, no bundler plugin needed for one script tag.
 */
declare global {
  interface Window {
    grecaptcha?: {
      render: (
        container: HTMLElement,
        params: {
          sitekey: string
          callback: (token: string) => void
          'expired-callback': () => void
        },
      ) => number
    }
    __onRecaptchaScriptLoad?: () => void
  }
}

let scriptLoadPromise: Promise<void> | null = null

function loadRecaptchaScript(): Promise<void> {
  scriptLoadPromise ??= new Promise((resolve) => {
    window.__onRecaptchaScriptLoad = () => resolve()
    const script = document.createElement('script')
    script.src =
      'https://www.google.com/recaptcha/api.js?onload=__onRecaptchaScriptLoad&render=explicit'
    script.async = true
    script.defer = true
    document.head.appendChild(script)
  })
  return scriptLoadPromise
}

export function Recaptcha({
  siteKey,
  onChange,
}: {
  siteKey: string
  onChange: (token: string | null) => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetIdRef = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false
    void loadRecaptchaScript().then(() => {
      if (cancelled || !containerRef.current || widgetIdRef.current !== null) return
      widgetIdRef.current = window.grecaptcha!.render(containerRef.current, {
        sitekey: siteKey,
        callback: onChange,
        'expired-callback': () => onChange(null),
      })
    })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [siteKey])

  return <div ref={containerRef} />
}
