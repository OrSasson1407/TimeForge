"""VerificationCodeRepository: persists in-flight registration codes,
keyed by the email being verified (docs/05-DATABASE.md, `emailVerifications`
collection). One active code per email — `save` overwrites any prior one,
matching "resend" semantics (the old code stops working the moment a new
one is issued).
"""

from typing import Protocol

from app.domain.models import EmailVerification


class VerificationCodeRepository(Protocol):
    def get(self, email: str) -> EmailVerification | None: ...

    def save(self, verification: EmailVerification) -> None: ...

    def record_attempt(self, email: str) -> int:
        """Increments and returns the attempt counter for `email`'s
        current code. Returns 0 if there is no code on file (already
        consumed or never issued) — callers should re-check `get` for
        that case rather than trust a bumped counter that doesn't exist."""
        ...

    def delete(self, email: str) -> None: ...
