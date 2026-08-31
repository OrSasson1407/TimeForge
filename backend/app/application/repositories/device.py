"""DeviceTokenRepository and PushSenderPort — the two seams the mobile
push feature needs.

Split deliberately: storing "who can be reached" is a persistence concern
with the same shape as every other repository here, while actually
delivering is a third-party network call. Keeping them apart means the
delivery side can be faked in tests without a live FCM project, the same
way `EmailSender` already is for SMTP.
"""

from typing import Protocol

from app.domain.models.device import DeviceToken


class DeviceTokenRepository(Protocol):
    def save(self, device: DeviceToken) -> None:
        """Idempotent upsert. Re-registering an existing token (every app
        launch does) must not create a duplicate."""
        ...

    def get(self, token: str) -> DeviceToken | None:
        """Needed to check ownership before an unregister: without it, any
        authenticated caller could delete a token belonging to someone
        else."""
        ...

    def list_for_school(self, school_id: str) -> list[DeviceToken]: ...

    def delete(self, token: str) -> None:
        """Used to prune tokens the push provider reports as permanently
        unregistered — an app uninstall leaves one behind forever
        otherwise."""
        ...


class PushSenderPort(Protocol):
    def send_to_tokens(self, tokens: list[str], *, title: str, body: str) -> list[str]:
        """Deliver to every token; return the ones that are permanently
        invalid so the caller can prune them.

        Returning failures rather than raising is deliberate: a push is a
        best-effort courtesy on top of an action that has already
        succeeded, so one unreachable handset must never turn a successful
        publish into an error.
        """
        ...
