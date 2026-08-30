"""Mocks the ONE true side-effecting boundary (the Firebase Admin SDK call
itself, docs/07-CODE_STANDARDS.md #23) — everything else (User lookup) uses
a real fake repository, not a mock.
"""

from unittest.mock import MagicMock, patch

import pytest
from firebase_admin.exceptions import FirebaseError

from app.core.errors import AuthenticationError
from app.domain.models import User, UserRole
from app.infrastructure.firebase.auth import resolve_user, verify_id_token
from tests.support.fakes import FakeUserRepository


def test_verify_id_token_returns_the_uid_on_success() -> None:
    fake_auth_client = MagicMock()
    fake_auth_client.verify_id_token.return_value = {"uid": "firebase_uid_123"}

    with patch("app.infrastructure.firebase.auth.get_auth_client", return_value=fake_auth_client):
        identity = verify_id_token("some-token")

    assert identity.uid == "firebase_uid_123"


def test_verify_id_token_wraps_firebase_errors_as_authentication_error() -> None:
    fake_auth_client = MagicMock()
    fake_auth_client.verify_id_token.side_effect = FirebaseError(
        code="INVALID_ARGUMENT", message="Token expired"
    )

    with (
        patch("app.infrastructure.firebase.auth.get_auth_client", return_value=fake_auth_client),
        pytest.raises(AuthenticationError, match="Token expired"),
    ):
        verify_id_token("expired-token")


def test_resolve_user_returns_the_matching_user_record() -> None:
    repo = FakeUserRepository()
    repo.save(User(id="firebase_uid_123", role=UserRole.ADMIN, school_id="s1", display_name="Dana"))
    fake_auth_client = MagicMock()
    fake_auth_client.verify_id_token.return_value = {"uid": "firebase_uid_123"}

    with patch("app.infrastructure.firebase.auth.get_auth_client", return_value=fake_auth_client):
        user = resolve_user("some-token", repo)

    assert user.id == "firebase_uid_123"
    assert user.role is UserRole.ADMIN


def test_resolve_user_rejects_a_verified_token_with_no_user_record() -> None:
    repo = FakeUserRepository()
    fake_auth_client = MagicMock()
    fake_auth_client.verify_id_token.return_value = {"uid": "unknown_uid"}

    with (
        patch("app.infrastructure.firebase.auth.get_auth_client", return_value=fake_auth_client),
        pytest.raises(AuthenticationError, match="No TimeForge user record"),
    ):
        resolve_user("some-token", repo)
