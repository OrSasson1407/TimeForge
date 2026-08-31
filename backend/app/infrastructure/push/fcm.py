"""Firebase Cloud Messaging push sender.

Uses `firebase_admin.messaging`, which the project already depends on for
Auth and Firestore — no new dependency, and it authenticates with the same
service account, so there is no second credential to provision.

Mirrors `app/infrastructure/email/sender.py`'s dev-fallback shape: with no
Firebase app configured the send is logged rather than attempted, so local
development and tests never need a real FCM project.
"""

import logging

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)

#: FCM's permanent-failure signals. `UnregisteredError` means the app was
#: uninstalled or the token was replaced; a malformed argument means the
#: token is not a token at all. Both are unrecoverable for that token
#: specifically, so it should be pruned rather than retried forever.
_PERMANENT_FAILURES = (messaging.UnregisteredError, messaging.SenderIdMismatchError, ValueError)


class FcmPushSender:
    """Sends one-by-one rather than via `send_each_for_multicast`, because
    the caller needs to know *which* tokens failed in order to prune them,
    and per-token attribution is exactly what a multicast response makes
    awkward. Push volume here is one message per schedule publish per
    device — a handful, not a broadcast campaign — so the simpler,
    attributable loop is the right trade."""

    def send_to_tokens(self, tokens: list[str], *, title: str, body: str) -> list[str]:
        invalid: list[str] = []
        for token in tokens:
            message = messaging.Message(
                token=token,
                notification=messaging.Notification(title=title, body=body),
            )
            try:
                messaging.send(message)
            except _PERMANENT_FAILURES:
                logger.info("Pruning permanently invalid push token")
                invalid.append(token)
            except FirebaseError as exc:
                # Transient (network, quota, FCM outage). Leave the token in
                # place: it is probably still good, and the next publish
                # will try again. Never re-raise — a push failure must not
                # fail the publish that triggered it.
                logger.warning("Push delivery failed, leaving token registered: %s", exc)
        return invalid


class LoggingPushSender:
    """Dev/test fallback: records nothing externally, just logs. Selected
    when no push credentials are configured."""

    def send_to_tokens(self, tokens: list[str], *, title: str, body: str) -> list[str]:
        logger.info("Push (not sent — no FCM configured) to %d device(s): %s", len(tokens), title)
        del body
        return []
