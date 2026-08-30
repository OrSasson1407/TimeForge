/** Mirrors backend/app/api/schemas/common.py — the structured error envelope
 * every non-2xx API response uses. */
export interface ErrorDetail {
  type: string
  message: string
  details: Record<string, unknown>
}

export interface ErrorEnvelope {
  error: ErrorDetail
}
