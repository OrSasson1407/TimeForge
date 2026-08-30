"""Structured error hierarchy (docs/04-DESIGN.md #24). The API layer (a
later phase) catches `DomainError` at its outermost boundary and maps each
subtype to `status_code` — callers below the API never format an HTTP
response themselves (docs/03-ARCHITECTURE.md #27, docs/01-CLAUDE.md #10).
"""

from typing import ClassVar


class DomainError(Exception):
    """Base of every structured error this backend raises on purpose. An
    *unexpected* exception is never a DomainError — it's caught separately
    at the API boundary and returned as a generic 500 without internal
    detail (docs/02-PRD.md #30)."""

    status_code: ClassVar[int] = 500

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(DomainError):
    """A request is structurally or semantically invalid."""

    status_code: ClassVar[int] = 400


class ConflictError(DomainError):
    """A requested change conflicts with the current state (e.g. a
    manual move rejected by a hard constraint)."""

    status_code: ClassVar[int] = 409


class AuthenticationError(DomainError):
    """The caller's identity could not be established at all: no
    credential, a malformed one, or one that failed Firebase verification
    (docs/03-ARCHITECTURE.md Edge Case #25). Distinct from
    AuthorizationError: this caller isn't a known principal yet, as
    opposed to a known one who lacks permission."""

    status_code: ClassVar[int] = 401


class AuthorizationError(DomainError):
    """The caller is authenticated but not permitted to perform this
    action (docs/03-ARCHITECTURE.md Edge Case #26)."""

    status_code: ClassVar[int] = 403


class NotFoundError(DomainError):
    """A referenced entity does not exist."""

    status_code: ClassVar[int] = 404


class SchedulingError(DomainError):
    """The solver reported FAILED (docs/04-DESIGN.md #14) — an unexpected
    internal failure during search, not a legitimate infeasibility."""

    status_code: ClassVar[int] = 422


class InfeasibleScheduleError(DomainError):
    """The solver reported INFEASIBLE. Carries the InfeasibilityResult in
    `details` so the API layer doesn't need a parallel error-payload shape."""

    status_code: ClassVar[int] = 422


class ReschedulingError(DomainError):
    """A disruption event could not be repaired (docs/04-DESIGN.md #17)."""

    status_code: ClassVar[int] = 422


class ConcurrencyError(DomainError):
    """An optimistic-concurrency write was rejected because the caller's
    `versionTag` was stale (docs/05-DATABASE.md #13) — never a silent
    overwrite (NFR-004)."""

    status_code: ClassVar[int] = 409


class RateLimitError(DomainError):
    """The caller exceeded a request-rate limit (registration, code
    resend, ...). Carries no internal detail beyond a retry hint —
    never reveals *why* a specific caller was throttled."""

    status_code: ClassVar[int] = 429
