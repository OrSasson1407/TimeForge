/** Mirrors backend/app/core/security.py's `validate_password_strength` — the
 * same five rules, checked live so a user sees what's missing before
 * submitting rather than after a round-trip. (The backend separately
 * checks the password against known data breaches — that one can't be
 * mirrored client-side without leaking the password to a third party, so
 * it only surfaces as a server error if it fails.) */
const RULES: { label: string; test: (password: string) => boolean }[] = [
  { label: 'At least 8 characters', test: (pw) => pw.length >= 8 },
  { label: 'A lowercase letter', test: (pw) => /[a-z]/.test(pw) },
  { label: 'An uppercase letter', test: (pw) => /[A-Z]/.test(pw) },
  { label: 'A digit', test: (pw) => /\d/.test(pw) },
  { label: 'A symbol (e.g. !@#$%)', test: (pw) => /[^A-Za-z0-9]/.test(pw) },
]

export function passwordMeetsAllRules(password: string): boolean {
  return RULES.every((rule) => rule.test(password))
}

export function PasswordStrengthMeter({ password }: { password: string }) {
  const metCount = RULES.filter((rule) => rule.test(password)).length
  const pct = (metCount / RULES.length) * 100
  const color =
    metCount === RULES.length
      ? 'var(--color-success)'
      : metCount >= 2
        ? 'var(--color-warning)'
        : 'var(--color-danger)'

  return (
    <div className="password-strength">
      <div className="password-strength-bar">
        <span style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <ul className="password-rules">
        {RULES.map((rule) => {
          const met = rule.test(password)
          return (
            <li key={rule.label} className={met ? 'met' : undefined}>
              {met ? '✓' : '○'} {rule.label}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
