"""IdentityAdminPort: the registration/approval flow's one dependency on
"create/find/delete a Firebase Auth account" — pulled out from the routers
into an injectable port for the same reason every other repository is
(docs/07-CODE_STANDARDS.md #21): so tests can substitute an in-memory fake
instead of calling the real Firebase Admin SDK. Distinct from
`UserRepository`: that one owns the Firestore `users` document (role,
school, teacher_id); this one owns the Firebase Auth account itself
(email, password, the emailVerified flag Firebase tracks on its side).
"""

from typing import Protocol


class IdentityAdminPort(Protocol):
    def create_user(self, *, email: str, password: str, display_name: str) -> str:
        """Returns the new account's uid. Raises ConflictError if an
        account with this email already exists."""
        ...

    def get_uid_by_email(self, email: str) -> str | None: ...

    def get_email(self, uid: str) -> str | None: ...

    def mark_email_verified(self, uid: str) -> None: ...

    def delete_user(self, uid: str) -> None: ...

    def set_disabled(self, uid: str, *, disabled: bool) -> None:
        """Best-effort: disables/re-enables the Firebase Auth account
        itself (a disabled account can't complete sign-in at all, or has
        its existing tokens revoked). The authoritative enforcement point
        is still `User.is_active` in Firestore, checked on every request
        (docs/03-ARCHITECTURE.md #23-24) — this is defense in depth, not
        the only thing standing between a suspended account and access."""
        ...

    def verify_token(self, token: str) -> str:
        """Verifies a Firebase Auth ID token and returns its uid. Raises
        AuthenticationError for any invalid/expired/malformed token. Used
        by the OAuth-completion flow, which needs a verified identity
        before any Firestore User record exists yet — unlike
        `get_current_user`, which requires one."""
        ...
