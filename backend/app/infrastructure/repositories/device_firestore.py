"""Firestore-backed DeviceTokenRepository (docs/05-DATABASE.md #10: clients
never write this collection — registration goes through the API so the
token is bound to a server-verified user, not a self-asserted one)."""

from datetime import UTC, datetime
from typing import Any

from google.cloud.firestore import Client

from app.domain.models.device import DevicePlatform, DeviceToken

_COLLECTION = "deviceTokens"


def _to_document(device: DeviceToken) -> dict[str, Any]:
    return {
        "token": device.token,
        "userId": device.user_id,
        "schoolId": device.school_id,
        "platform": device.platform.value,
        "registeredAt": device.registered_at,
    }


def _from_document(data: dict[str, Any]) -> DeviceToken:
    registered_at = data.get("registeredAt")
    return DeviceToken(
        token=data["token"],
        user_id=data["userId"],
        school_id=data["schoolId"],
        platform=DevicePlatform(data["platform"]),
        registered_at=registered_at if isinstance(registered_at, datetime) else datetime.now(UTC),
    )


class FirestoreDeviceTokenRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def save(self, device: DeviceToken) -> None:
        # set() on the token-keyed document is the idempotent upsert the
        # protocol requires: an app re-registering the same token on every
        # launch just rewrites the same document.
        self._client.collection(_COLLECTION).document(device.token).set(_to_document(device))

    def get(self, token: str) -> DeviceToken | None:
        snapshot = self._client.collection(_COLLECTION).document(token).get()
        if not snapshot.exists:
            return None
        return _from_document(snapshot.to_dict() or {})

    def list_for_school(self, school_id: str) -> list[DeviceToken]:
        query = self._client.collection(_COLLECTION).where("schoolId", "==", school_id)
        return [_from_document(doc.to_dict() or {}) for doc in query.stream()]

    def delete(self, token: str) -> None:
        self._client.collection(_COLLECTION).document(token).delete()
