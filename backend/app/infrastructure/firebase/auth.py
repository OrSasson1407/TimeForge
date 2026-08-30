"""ID token verification (docs/03-ARCHITECTURE.md #23-24): resolves a
Firebase Auth ID token to the backend's own `User` record. The token's
`uid` is Firebase-signature-verified; the ROLE always comes from
Firestore via `UserRepository`, never trusted from a client-supplied
claim (docs/01-CLAUDE.md rule 6, docs/03-ARCHITECTURE.md #23).
"""

import contextlib
from dataclasses import dataclass

from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError

from app.application.repositories import UserRepository
from app.core.errors import AuthenticationError, ConflictError
from app.domain.models import User
from app.infrastructure.firebase.client import get_auth_client


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    uid: str


def verify_id_token(id_token: str) -> VerifiedIdentity:
    """Raises AuthenticationError for any invalid, expired, revoked, or
    otherwise unverifiable token — `firebase_admin.exceptions.FirebaseError`
    is the common base every specific token error (InvalidIdTokenError,
    ExpiredIdTokenError, RevokedIdTokenError, ...) inherits from."""
    auth_client = get_auth_client()
    try:
        decoded = auth_client.verify_id_token(id_token)
    except FirebaseError as exc:
        raise AuthenticationError(f"Invalid or expired ID token: {exc}") from exc
    return VerifiedIdentity(uid=decoded["uid"])


def resolve_user(id_token: str, user_repository: UserRepository) -> User:
    """The full request-authentication step: verify the token, then look
    up the backend's own authorization record for that uid. A verified
    token with no matching User still can't be authenticated as a
    TimeForge principal — TimeForge doesn't auto-provision accounts from
    an unrecognized Firebase identity. A suspended account (`is_active`
    False) is rejected here too — the authoritative enforcement point for
    account deactivation, independent of whether the Firebase Auth account
    itself was also successfully disabled (best-effort, defense in depth;
    see `IdentityAdminPort.set_disabled`)."""
    identity = verify_id_token(id_token)
    user = user_repository.get(identity.uid)
    if user is None:
        raise AuthenticationError(f"No TimeForge user record for uid {identity.uid}")
    if not user.is_active:
        raise AuthenticationError("This account has been suspended")
    return user


class FirebaseIdentityAdmin:
    """Firebase-backed `IdentityAdminPort` (docs/03-ARCHITECTURE.md #23):
    the registration flow's account-creation/lookup/cleanup operations
    against the real Firebase Auth Admin SDK. Every method here swallows
    FirebaseError for cleanup operations (mark_email_verified,
    delete_user) — those are best-effort side effects; the Firestore
    User record is what the rest of the app actually trusts."""

    def create_user(self, *, email: str, password: str, display_name: str) -> str:
        try:
            record = get_auth_client().create_user(
                email=email, password=password, display_name=display_name
            )
        except firebase_auth.EmailAlreadyExistsError as exc:
            raise ConflictError("An account with this email already exists") from exc
        return record.uid

    def get_uid_by_email(self, email: str) -> str | None:
        try:
            return get_auth_client().get_user_by_email(email).uid
        except firebase_auth.UserNotFoundError:
            return None

    def get_email(self, uid: str) -> str | None:
        try:
            return get_auth_client().get_user(uid).email
        except FirebaseError:
            return None

    def mark_email_verified(self, uid: str) -> None:
        with contextlib.suppress(FirebaseError):
            get_auth_client().update_user(uid, email_verified=True)

    def delete_user(self, uid: str) -> None:
        with contextlib.suppress(FirebaseError):
            get_auth_client().delete_user(uid)

    def set_disabled(self, uid: str, *, disabled: bool) -> None:
        with contextlib.suppress(FirebaseError):
            get_auth_client().update_user(uid, disabled=disabled)

    def verify_token(self, token: str) -> str:
        return verify_id_token(token).uid
