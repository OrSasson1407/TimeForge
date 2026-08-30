"""EmailVerification entity: an in-flight registration code (docs/05-DATABASE.md
Users collection note on `emailVerifications`). Keyed by the email being
verified, not by user id — it exists before the Firestore User's identity
is fully trusted, and is deleted once consumed.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EmailVerification:
    email: str
    code_hash: str
    expires_at: datetime
    attempts: int = 0

    def __post_init__(self) -> None:
        if not self.email:
            raise ValueError("EmailVerification.email must not be empty")
        if not self.code_hash:
            raise ValueError("EmailVerification.code_hash must not be empty")
        if self.attempts < 0:
            raise ValueError("EmailVerification.attempts must not be negative")

    def is_expired(self, *, now: datetime) -> bool:
        return now >= self.expires_at
